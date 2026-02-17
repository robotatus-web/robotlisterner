"""Vector store layer — wraps ChromaDB for semantic search over RF artifacts."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from rf_rag.config import RAGConfig
from rf_rag.models import KeywordDef, ResourceFile, TestCaseDef

logger = logging.getLogger(__name__)


def _doc_id(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


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
    """Semantic vector store backed by ChromaDB with sentence-transformers embeddings."""

    def __init__(self, cfg: RAGConfig) -> None:
        self._cfg = cfg
        persist_dir = str(cfg.effective_data_dir() / "chroma_db")

        self._client = chromadb.Client(ChromaSettings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_dir,
            anonymized_telemetry=False,
        ))

        # We'll use ChromaDB's default embedding function (all-MiniLM-L6-v2)
        # or a custom sentence-transformers one
        try:
            from chromadb.utils import embedding_functions
            self._ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=cfg.embedding_model,
            )
        except Exception:
            logger.warning("SentenceTransformer embedding not available; using default")
            self._ef = None

        self._collection = self._client.get_or_create_collection(
            name=cfg.chroma_collection,
            embedding_function=self._ef,
        )

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def index_file(self, rf: ResourceFile) -> int:
        """Index all keywords and test cases from a ResourceFile. Returns count added."""
        docs: list[str] = []
        metas: list[dict[str, Any]] = []
        ids: list[str] = []

        for kw in rf.keywords:
            text = _build_embedding_text(kw.documentation, kw.body_text, kw.name)
            doc_id = _doc_id(f"kw:{kw.fqn}")
            docs.append(text)
            metas.append({
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
            docs.append(text)
            metas.append({
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
            docs.append(rf.documentation)
            metas.append({
                "type": "file_doc",
                "fqn": rf.rel_path,
                "name": Path(rf.rel_path).stem,
                "source": rf.rel_path,
                "role": rf.role.value,
                "platform": rf.platform.value,
                "tags": "",
            })
            ids.append(doc_id)

        if docs:
            self._collection.upsert(documents=docs, metadatas=metas, ids=ids)

        return len(docs)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def search(self, query: str, n_results: int = 10,
               where: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Semantic search. Returns list of {id, document, metadata, distance}."""
        kwargs: dict[str, Any] = {
            "query_texts": [query],
            "n_results": min(n_results, self._collection.count() or 1),
        }
        if where:
            kwargs["where"] = where

        results = self._collection.query(**kwargs)

        output: list[dict[str, Any]] = []
        for i in range(len(results["ids"][0])):
            output.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0.0,
            })
        return output

    def get_all_embeddings(self, where: dict[str, Any] | None = None) -> dict[str, list[float]]:
        """Return {id: embedding_vector} for all (or filtered) items."""
        kwargs: dict[str, Any] = {"include": ["embeddings", "metadatas"]}
        if where:
            kwargs["where"] = where
        data = self._collection.get(**kwargs)
        result: dict[str, list[float]] = {}
        if data["ids"] and data["embeddings"]:
            for uid, emb in zip(data["ids"], data["embeddings"]):
                result[uid] = emb
        return result

    def get_metadata(self, doc_id: str) -> dict[str, Any]:
        data = self._collection.get(ids=[doc_id], include=["metadatas"])
        if data["metadatas"]:
            return data["metadatas"][0]
        return {}

    def count(self) -> int:
        return self._collection.count()

    def clear(self) -> None:
        """Delete all documents from the collection."""
        self._client.delete_collection(self._cfg.chroma_collection)
        self._collection = self._client.get_or_create_collection(
            name=self._cfg.chroma_collection,
            embedding_function=self._ef,
        )
