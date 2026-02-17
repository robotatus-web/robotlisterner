"""Module 1: Multi-Layer Redundancy Detection.

Detection layers:
  - Horizontal: identical setup/Base Data Creation across suites.
  - Vertical: AtomicTests that are fully covered by an SIT/E2E test.
  - Migration Sync: migration tests covered by main suite or SIT.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from rf_rag.graph import RFGraph
from rf_rag.models import FileRole, ResourceFile
from rf_rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class RedundancyHit:
    """One detected redundancy."""

    kind: str  # horizontal | vertical | migration_sync
    source_fqn: str
    duplicate_fqn: str
    similarity: float
    recommendation: str


@dataclass
class RedundancyReport:
    hits: list[RedundancyHit] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        by_kind: dict[str, int] = {}
        for h in self.hits:
            by_kind[h.kind] = by_kind.get(h.kind, 0) + 1
        return {"total": len(self.hits), "by_kind": by_kind}


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


class RedundancyDetector:
    """Detects multi-layer redundancy across the RF project."""

    def __init__(
        self,
        graph: RFGraph,
        vector_store: VectorStore,
        file_map: dict[str, ResourceFile],
        similarity_threshold: float = 0.90,
    ) -> None:
        self._graph = graph
        self._vs = vector_store
        self._file_map = file_map
        self._threshold = similarity_threshold

    def detect(self) -> RedundancyReport:
        report = RedundancyReport()
        self._horizontal(report)
        self._vertical(report)
        self._migration_sync(report)
        return report

    # ------------------------------------------------------------------
    # Horizontal: same setup logic across suites
    # ------------------------------------------------------------------

    def _horizontal(self, report: RedundancyReport) -> None:
        """Find identical Base Data Creation / setup keywords across suites."""
        setup_keywords: list[tuple[str, str]] = []  # (fqn, doc_id)

        embeddings = self._vs.get_all_embeddings(where={"type": "keyword"})
        meta_cache: dict[str, dict] = {}

        for doc_id in embeddings:
            meta = self._vs.get_metadata(doc_id)
            meta_cache[doc_id] = meta
            name = meta.get("name", "").lower()
            if "base data creation" in name or "setup" in name:
                setup_keywords.append((meta.get("fqn", ""), doc_id))

        # Pairwise comparison
        for i, (fqn_a, id_a) in enumerate(setup_keywords):
            for fqn_b, id_b in setup_keywords[i + 1:]:
                # Skip same-file comparisons
                src_a = meta_cache[id_a].get("source", "")
                src_b = meta_cache[id_b].get("source", "")
                if src_a == src_b:
                    continue

                sim = _cosine_similarity(embeddings[id_a], embeddings[id_b])
                if sim >= self._threshold:
                    report.hits.append(RedundancyHit(
                        kind="horizontal",
                        source_fqn=fqn_a,
                        duplicate_fqn=fqn_b,
                        similarity=sim,
                        recommendation=(
                            f"Extract shared setup logic into a common resource keyword. "
                            f"Similarity: {sim:.2%}"
                        ),
                    ))

    # ------------------------------------------------------------------
    # Vertical: atomic tests covered by SIT
    # ------------------------------------------------------------------

    def _vertical(self, report: RedundancyReport) -> None:
        """Flag atomic tests whose flow is fully covered by an E2E/SIT test."""
        atomic_ids: list[tuple[str, str]] = []
        sit_ids: list[tuple[str, str]] = []

        embeddings = self._vs.get_all_embeddings(where={"type": "test_case"})

        for doc_id in embeddings:
            meta = self._vs.get_metadata(doc_id)
            role = meta.get("role", "")
            fqn = meta.get("fqn", "")
            if role == FileRole.ATOMIC_TEST.value:
                atomic_ids.append((fqn, doc_id))
            elif role == FileRole.E2E_TEST.value:
                sit_ids.append((fqn, doc_id))

        for fqn_a, id_a in atomic_ids:
            for fqn_s, id_s in sit_ids:
                sim = _cosine_similarity(embeddings[id_a], embeddings[id_s])
                if sim >= self._threshold:
                    report.hits.append(RedundancyHit(
                        kind="vertical",
                        source_fqn=fqn_a,
                        duplicate_fqn=fqn_s,
                        similarity=sim,
                        recommendation=(
                            f"Atomic test '{fqn_a}' appears fully covered by "
                            f"SIT test '{fqn_s}'. Consider deprecation. "
                            f"Similarity: {sim:.2%}"
                        ),
                    ))

    # ------------------------------------------------------------------
    # Migration sync
    # ------------------------------------------------------------------

    def _migration_sync(self, report: RedundancyReport) -> None:
        """Recommend deprecation of migration tests covered by main/SIT suites."""
        migration_ids: list[tuple[str, str]] = []
        other_ids: list[tuple[str, str]] = []

        embeddings = self._vs.get_all_embeddings(where={"type": "test_case"})

        for doc_id in embeddings:
            meta = self._vs.get_metadata(doc_id)
            role = meta.get("role", "")
            fqn = meta.get("fqn", "")
            if role == FileRole.MIGRATION_TEST.value:
                migration_ids.append((fqn, doc_id))
            elif role in (FileRole.ATOMIC_TEST.value, FileRole.E2E_TEST.value):
                other_ids.append((fqn, doc_id))

        for fqn_m, id_m in migration_ids:
            for fqn_o, id_o in other_ids:
                sim = _cosine_similarity(embeddings[id_m], embeddings[id_o])
                if sim >= self._threshold:
                    report.hits.append(RedundancyHit(
                        kind="migration_sync",
                        source_fqn=fqn_m,
                        duplicate_fqn=fqn_o,
                        similarity=sim,
                        recommendation=(
                            f"Migration test '{fqn_m}' is covered by '{fqn_o}'. "
                            f"Consider deprecation. Similarity: {sim:.2%}"
                        ),
                    ))
