"""Vector store layer — wraps Qdrant for semantic search over RF artifacts."""

from __future__ import annotations

import hashlib
import logging
import uuid
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from rf_rag.config import RAGConfig
from rf_rag.models import KeywordDef, ResourceFile, TestCaseDef

logger = logging.getLogger(__name__)


def _doc_id(text: str) -> str:
    """Generate a deterministic UUID-formatted string ID from text."""
    h = hashlib.sha256(text.encode()).hexdigest()[:32]
    return str(uuid.UUID(h))


def _build_embedding_text(doc: str, body: str, name: str) -> str:
    """Build the text that will be embedded.

    Priority: documentation > body > name.
    Per spec, [Documentation] blocks are the primary embedding source.
    """
    parts: list[str] = []
    if doc:
        parts.append(doc)
    if body:
        parts.append(body)
    if name and name not in (doc or ""):
        parts.append(name)
    return "\n".join(parts) if parts else name


class VectorStore:
    """Semantic vector store backed by Qdrant with sentence-transformers embeddings."""

    def __init__(self, cfg: RAGConfig) -> None:
        self._cfg = cfg

        # Load embedding model
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(cfg.embedding_model)
        except Exception:
            logger.warning("SentenceTransformer not available; embeddings disabled")
            self._model = None

        # Connect to Qdrant
        if cfg.qdrant_url:
            self._client = QdrantClient(url=cfg.qdrant_url)
        elif cfg.qdrant_path:
            self._client = QdrantClient(path=cfg.qdrant_path)
        else:
            self._client = QdrantClient(location=":memory:")

        self._collection = cfg.qdrant_collection
        self._dim = cfg.embedding_dim
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create the collection if it does not exist."""
        if not self._client.collection_exists(self._collection):
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=self._dim, distance=Distance.COSINE),
            )

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """Compute embeddings for a list of texts."""
        if self._model is None:
            return [[0.0] * self._dim for _ in texts]
        vectors = self._model.encode(texts)
        return [v.tolist() for v in vectors]

    @staticmethod
    def _build_filter(where: dict[str, Any] | None) -> Filter | None:
        """Convert a simple {key: value} filter dict to a Qdrant Filter."""
        if not where:
            return None
        conditions = [
            FieldCondition(key=k, match=MatchValue(value=v))
            for k, v in where.items()
        ]
        return Filter(must=conditions)

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def index_file(self, rf: ResourceFile) -> int:
        """Index all keywords and test cases from a ResourceFile. Returns count added."""
        texts: list[str] = []
        payloads: list[dict[str, Any]] = []
        ids: list[str] = []

        for kw in rf.keywords:
            text = _build_embedding_text(kw.documentation, kw.body_text, kw.name)
            doc_id = _doc_id(f"kw:{kw.fqn}")
            texts.append(text)
            payloads.append({
                "type": "keyword",
                "fqn": kw.fqn,
                "name": kw.name,
                "source": rf.rel_path,
                "role": rf.role.value,
                "platform": rf.platform.value,
                "tags": ",".join(kw.tags),
            })
            ids.append(doc_id)

        for tc in rf.test_cases:
            text = _build_embedding_text(tc.documentation, tc.body_text, tc.name)
            doc_id = _doc_id(f"tc:{tc.fqn}")
            texts.append(text)
            payloads.append({
                "type": "test_case",
                "fqn": tc.fqn,
                "name": tc.name,
                "source": rf.rel_path,
                "role": rf.role.value,
                "platform": rf.platform.value,
                "tags": ",".join(tc.tags),
            })
            ids.append(doc_id)

        # Also embed file-level documentation if non-empty
        if rf.documentation:
            doc_id = _doc_id(f"file:{rf.rel_path}")
            texts.append(rf.documentation)
            payloads.append({
                "type": "file_doc",
                "fqn": rf.rel_path,
                "name": Path(rf.rel_path).stem,
                "source": rf.rel_path,
                "role": rf.role.value,
                "platform": rf.platform.value,
                "tags": "",
            })
            ids.append(doc_id)

        if texts:
            vectors = self._embed(texts)
            points = [
                PointStruct(
                    id=uid,
                    vector=vec,
                    payload={**meta, "_document": doc_text},
                )
                for uid, vec, meta, doc_text in zip(ids, vectors, payloads, texts)
            ]
            self._client.upsert(collection_name=self._collection, points=points)

        return len(texts)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        n_results: int = 10,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Semantic search. Returns list of {id, document, metadata, distance}."""
        query_vector = self._embed([query])[0]
        qfilter = self._build_filter(where)

        total = self._client.count(collection_name=self._collection).count
        limit = min(n_results, total) if total > 0 else 1

        response = self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            limit=limit,
            query_filter=qfilter,
            with_payload=True,
        )

        output: list[dict[str, Any]] = []
        for hit in response.points:
            payload = dict(hit.payload or {})
            document = payload.pop("_document", "")
            output.append({
                "id": hit.id,
                "document": document,
                "metadata": payload,
                "distance": 1.0 - hit.score,
            })
        return output

    def get_all_embeddings(
        self, where: dict[str, Any] | None = None
    ) -> dict[str, list[float]]:
        """Return {id: embedding_vector} for all (or filtered) items."""
        qfilter = self._build_filter(where)
        result: dict[str, list[float]] = {}

        offset = None
        while True:
            points, next_offset = self._client.scroll(
                collection_name=self._collection,
                scroll_filter=qfilter,
                limit=1000,
                offset=offset,
                with_vectors=True,
                with_payload=False,
            )
            for point in points:
                result[point.id] = point.vector
            if next_offset is None:
                break
            offset = next_offset

        return result

    def get_metadata(self, doc_id: str) -> dict[str, Any]:
        points = self._client.retrieve(
            collection_name=self._collection,
            ids=[doc_id],
            with_payload=True,
            with_vectors=False,
        )
        if points:
            payload = dict(points[0].payload or {})
            payload.pop("_document", None)
            return payload
        return {}

    def count(self) -> int:
        return self._client.count(collection_name=self._collection).count

    def clear(self) -> None:
        """Delete all documents from the collection."""
        self._client.delete_collection(self._collection)
        self._ensure_collection()
