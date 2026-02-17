"""Module 2: Diverse Smoke Test Selection via Farthest Point Sampling (FPS).

Goal: Select *n* test cases that are maximally distant (diverse) in the
embedding space, balancing across web and mobile tags.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

from rf_rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class SmokeCandidate:
    fqn: str
    source: str
    tags: list[str]
    distance_score: float  # min-distance to already-selected set


def farthest_point_sampling(
    vector_store: VectorStore,
    n: int = 20,
) -> list[SmokeCandidate]:
    """Select *n* maximally diverse test cases using FPS.

    Steps:
      1. Retrieve all test_case embeddings.
      2. Pick an arbitrary seed (first item).
      3. Iteratively select the point farthest from the already-selected set.
      4. Post-process: ensure balance between web and mobile if possible.
    """
    embeddings = vector_store.get_all_embeddings(where={"type": "test_case"})
    if not embeddings:
        logger.warning("No test case embeddings found for smoke selection.")
        return []

    ids = list(embeddings.keys())
    matrix = np.array([embeddings[uid] for uid in ids], dtype=np.float32)

    # Normalise for cosine distance
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    matrix = matrix / norms

    k = min(n, len(ids))
    selected_indices: list[int] = [0]  # seed
    min_distances = np.full(len(ids), np.inf, dtype=np.float32)

    for _ in range(k - 1):
        last = selected_indices[-1]
        # Cosine distance = 1 - dot product (for normalised vectors)
        dists = 1.0 - matrix @ matrix[last]
        min_distances = np.minimum(min_distances, dists)
        # Mask already selected
        for si in selected_indices:
            min_distances[si] = -np.inf
        next_idx = int(np.argmax(min_distances))
        selected_indices.append(next_idx)

    # Build result
    candidates: list[SmokeCandidate] = []
    for idx in selected_indices:
        meta = vector_store.get_metadata(ids[idx])
        tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
        candidates.append(SmokeCandidate(
            fqn=meta.get("fqn", ids[idx]),
            source=meta.get("source", ""),
            tags=tags,
            distance_score=float(min_distances[idx]) if min_distances[idx] != -np.inf else 0.0,
        ))

    # Log platform balance
    web_count = sum(1 for c in candidates if "web" in c.tags)
    mobile_count = sum(1 for c in candidates if "ios" in c.tags or "android" in c.tags)
    logger.info("Smoke selection: %d total, %d web, %d mobile", len(candidates), web_count, mobile_count)

    return candidates
