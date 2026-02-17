"""Module 3: Intelligent Query & Inventory.

Provides a unified query interface across the Graph and Vector layers
for natural-language and structured queries.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from rf_rag.graph import RFGraph
from rf_rag.models import FileRole, ResourceFile
from rf_rag.resolver import ResourceResolver
from rf_rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result of an inventory or search query."""

    answer: str = ""
    items: list[dict[str, Any]] = field(default_factory=list)
    count: int = 0


class QueryEngine:
    """Combines Graph + Vector queries to answer natural-language questions."""

    def __init__(
        self,
        graph: RFGraph,
        vector_store: VectorStore,
        file_map: dict[str, ResourceFile],
        resolver: ResourceResolver,
    ) -> None:
        self._graph = graph
        self._vs = vector_store
        self._file_map = file_map
        self._resolver = resolver

    # ------------------------------------------------------------------
    # Structured queries (graph-based)
    # ------------------------------------------------------------------

    def count_by_role(self) -> dict[str, int]:
        """Count files per role."""
        counts: dict[str, int] = {}
        for rf in self._file_map.values():
            key = rf.role.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def graphql_mutations_without_sit(self) -> QueryResult:
        """Find GraphQL mutation keywords that have no SIT coverage.

        A mutation keyword (in resources/**/api/) is "covered" if at least one
        SIT/E2E test case (directly or transitively) calls it.
        """
        api_keywords: list[str] = []
        for rf in self._file_map.values():
            if rf.role == FileRole.API:
                for kw in rf.keywords:
                    if "mutation" in kw.name.lower() or "mutation" in kw.documentation.lower():
                        api_keywords.append(kw.fqn)

        uncovered: list[dict[str, Any]] = []
        for fqn in api_keywords:
            callers = self._graph.callers_of(fqn)
            has_sit = False
            for caller in callers:
                node_data = self._graph.node_data(caller)
                if node_data.get("node_type") == "test_case":
                    src = node_data.get("source", "")
                    rf = self._file_map.get(src)
                    if rf and rf.role == FileRole.E2E_TEST:
                        has_sit = True
                        break
                # Also check if a caller keyword is itself called from a SIT test
                indirect_callers = self._graph.callers_of(caller)
                for ic in indirect_callers:
                    ic_data = self._graph.node_data(ic)
                    if ic_data.get("node_type") == "test_case":
                        src2 = ic_data.get("source", "")
                        rf2 = self._file_map.get(src2)
                        if rf2 and rf2.role == FileRole.E2E_TEST:
                            has_sit = True
                            break
                if has_sit:
                    break

            if not has_sit:
                uncovered.append({"fqn": fqn, "callers": callers})

        return QueryResult(
            answer=f"{len(uncovered)} GraphQL mutations lack SIT coverage.",
            items=uncovered,
            count=len(uncovered),
        )

    def mismatched_po_keys(self) -> QueryResult:
        """Find PO elements where iOS and Android dictionaries have mismatched keys."""
        mismatches = self._graph.mismatched_po_elements()
        return QueryResult(
            answer=f"{len(mismatches)} PO elements have mismatched iOS/Android keys.",
            items=mismatches,
            count=len(mismatches),
        )

    def keyword_inventory(self) -> QueryResult:
        """Full inventory of all keywords grouped by source file."""
        inventory: dict[str, list[str]] = {}
        for rf in self._file_map.values():
            if rf.keywords:
                inventory[rf.rel_path] = [kw.fqn for kw in rf.keywords]

        items = [{"file": k, "keywords": v} for k, v in sorted(inventory.items())]
        total = sum(len(v) for v in inventory.values())
        return QueryResult(
            answer=f"{total} keywords across {len(inventory)} files.",
            items=items,
            count=total,
        )

    def test_inventory(self) -> QueryResult:
        """Full inventory of all test cases grouped by role."""
        by_role: dict[str, list[str]] = {}
        for rf in self._file_map.values():
            for tc in rf.test_cases:
                role = rf.role.value
                by_role.setdefault(role, []).append(tc.fqn)

        items = [{"role": k, "tests": v} for k, v in sorted(by_role.items())]
        total = sum(len(v) for v in by_role.values())
        return QueryResult(
            answer=f"{total} test cases across {len(by_role)} roles.",
            items=items,
            count=total,
        )

    def effective_scope(self, rel_path: str) -> QueryResult:
        """Show all keywords available in the effective scope of a file."""
        keywords = self._resolver.effective_keywords(rel_path)
        items = [{"fqn": kw.fqn, "source": kw.source_file, "doc": kw.documentation}
                 for kw in keywords]
        return QueryResult(
            answer=f"{len(keywords)} keywords in effective scope of '{rel_path}'.",
            items=items,
            count=len(keywords),
        )

    # ------------------------------------------------------------------
    # Semantic search (vector-based)
    # ------------------------------------------------------------------

    def semantic_search(self, query: str, n: int = 10) -> QueryResult:
        """Free-text semantic search across all indexed RF artifacts."""
        results = self._vs.search(query, n_results=n)
        items = [
            {
                "fqn": r["metadata"].get("fqn", ""),
                "type": r["metadata"].get("type", ""),
                "source": r["metadata"].get("source", ""),
                "distance": r["distance"],
                "snippet": r["document"][:200],
            }
            for r in results
        ]
        return QueryResult(
            answer=f"Found {len(items)} results for '{query}'.",
            items=items,
            count=len(items),
        )
