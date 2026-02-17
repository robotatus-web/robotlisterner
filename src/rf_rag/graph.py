"""Graph layer — stores structural relationships using NetworkX."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import networkx as nx

from rf_rag.models import EdgeType, GraphEdge, ResourceFile

logger = logging.getLogger(__name__)


class RFGraph:
    """In-memory directed graph of the Robot Framework project structure.

    Node types (stored as ``node_type`` attr):
        ``file``, ``keyword``, ``test_case``, ``variable``, ``tag``,
        ``locator_element``

    Edge types follow :class:`rf_rag.models.EdgeType`.
    """

    def __init__(self) -> None:
        self.g = nx.DiGraph()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def add_file(self, rf: ResourceFile) -> None:
        """Ingest one parsed ResourceFile into the graph."""
        fnode = rf.rel_path
        self.g.add_node(fnode, node_type="file", role=rf.role.value,
                        platform=rf.platform.value, doc=rf.documentation)

        # --- Resource imports (IMPORTS edges) ---
        for imp in rf.imports:
            self.g.add_node(imp, node_type="file")
            self.g.add_edge(fnode, imp, edge_type=EdgeType.IMPORTS.value)

        # --- Keywords ---
        for kw in rf.keywords:
            kw_node = kw.fqn
            self.g.add_node(kw_node, node_type="keyword", doc=kw.documentation,
                            source=rf.rel_path, line=kw.line_number)
            self.g.add_edge(fnode, kw_node, edge_type=EdgeType.DEFINES.value)

            # Calls edges
            for called in kw.called_keywords:
                self.g.add_edge(kw_node, called, edge_type=EdgeType.CALLS.value)

            # Tags
            for tag in kw.tags:
                tag_node = f"tag:{tag}"
                self.g.add_node(tag_node, node_type="tag")
                self.g.add_edge(kw_node, tag_node, edge_type=EdgeType.TAGGED.value)

        # --- Test cases ---
        for tc in rf.test_cases:
            tc_node = tc.fqn
            self.g.add_node(tc_node, node_type="test_case", doc=tc.documentation,
                            source=rf.rel_path, line=tc.line_number)
            self.g.add_edge(fnode, tc_node, edge_type=EdgeType.TESTS.value)

            for called in tc.called_keywords:
                self.g.add_edge(tc_node, called, edge_type=EdgeType.CALLS.value)

            for tag in tc.tags:
                tag_node = f"tag:{tag}"
                self.g.add_node(tag_node, node_type="tag")
                self.g.add_edge(tc_node, tag_node, edge_type=EdgeType.TAGGED.value)

        # --- Variables ---
        for v in rf.variables:
            var_node = f"var:{v.name}"
            self.g.add_node(var_node, node_type="variable", source=rf.rel_path,
                            var_type=v.var_type)
            self.g.add_edge(fnode, var_node, edge_type=EdgeType.DEFINES.value)

        # --- Locator mappings ---
        for lm in rf.locator_mappings:
            el_node = f"element:{lm.element_name}"
            self.g.add_node(el_node, node_type="locator_element",
                            ios=lm.ios_locator or "", android=lm.android_locator or "")
            self.g.add_edge(fnode, el_node, edge_type=EdgeType.MAPS_ELEMENT.value)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def files_by_role(self, role: str) -> list[str]:
        return [n for n, d in self.g.nodes(data=True)
                if d.get("node_type") == "file" and d.get("role") == role]

    def keywords_in_file(self, rel_path: str) -> list[str]:
        return [t for _, t, d in self.g.out_edges(rel_path, data=True)
                if d.get("edge_type") == EdgeType.DEFINES.value
                and self.g.nodes[t].get("node_type") == "keyword"]

    def test_cases_in_file(self, rel_path: str) -> list[str]:
        return [t for _, t, d in self.g.out_edges(rel_path, data=True)
                if d.get("edge_type") == EdgeType.TESTS.value]

    def callers_of(self, keyword_fqn: str) -> list[str]:
        """Return nodes that call the given keyword."""
        return [s for s, _, d in self.g.in_edges(keyword_fqn, data=True)
                if d.get("edge_type") == EdgeType.CALLS.value]

    def callees_of(self, node: str) -> list[str]:
        return [t for _, t, d in self.g.out_edges(node, data=True)
                if d.get("edge_type") == EdgeType.CALLS.value]

    def all_test_cases(self) -> list[str]:
        return [n for n, d in self.g.nodes(data=True) if d.get("node_type") == "test_case"]

    def all_keywords(self) -> list[str]:
        return [n for n, d in self.g.nodes(data=True) if d.get("node_type") == "keyword"]

    def tags_of(self, node: str) -> list[str]:
        return [t.removeprefix("tag:") for _, t, d in self.g.out_edges(node, data=True)
                if d.get("edge_type") == EdgeType.TAGGED.value]

    def mismatched_po_elements(self) -> list[dict[str, Any]]:
        """Find locator elements that exist in one platform dict but not the other."""
        mismatches = []
        for n, d in self.g.nodes(data=True):
            if d.get("node_type") != "locator_element":
                continue
            ios = d.get("ios", "")
            android = d.get("android", "")
            if bool(ios) != bool(android):
                mismatches.append({
                    "element": n.removeprefix("element:"),
                    "ios": ios or "MISSING",
                    "android": android or "MISSING",
                })
        return mismatches

    def node_data(self, node: str) -> dict[str, Any]:
        if node in self.g:
            return dict(self.g.nodes[node])
        return {}

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Path) -> None:
        data = nx.node_link_data(self.g)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info("Graph saved to %s (%d nodes, %d edges)",
                     path, self.g.number_of_nodes(), self.g.number_of_edges())

    def load(self, path: Path) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        self.g = nx.node_link_graph(data)
        logger.info("Graph loaded from %s (%d nodes, %d edges)",
                     path, self.g.number_of_nodes(), self.g.number_of_edges())

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def summary(self) -> dict[str, int]:
        types: dict[str, int] = {}
        for _, d in self.g.nodes(data=True):
            t = d.get("node_type", "unknown")
            types[t] = types.get(t, 0) + 1
        return {
            "total_nodes": self.g.number_of_nodes(),
            "total_edges": self.g.number_of_edges(),
            **{f"nodes_{k}": v for k, v in sorted(types.items())},
        }
