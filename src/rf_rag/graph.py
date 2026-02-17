"""Graph layer — stores structural relationships using Neo4j."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from neo4j import GraphDatabase

from rf_rag.models import EdgeType, ResourceFile

logger = logging.getLogger(__name__)

# Node labels used in Neo4j
_LABELS = ("File", "Keyword", "TestCase", "Variable", "Tag", "LocatorElement")

# Mapping from internal node_type strings to Neo4j labels
_TYPE_TO_LABEL = {
    "file": "File",
    "keyword": "Keyword",
    "test_case": "TestCase",
    "variable": "Variable",
    "tag": "Tag",
    "locator_element": "LocatorElement",
}


class RFGraph:
    """Neo4j-backed directed graph of the Robot Framework project structure.

    Node labels:
        ``File``, ``Keyword``, ``TestCase``, ``Variable``, ``Tag``,
        ``LocatorElement``

    Relationship types follow :class:`rf_rag.models.EdgeType`.
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        auth: tuple[str, str] = ("neo4j", "neo4j"),
        database: str = "neo4j",
    ) -> None:
        self._driver = GraphDatabase.driver(uri, auth=auth)
        self._db = database
        self._ensure_constraints()

    def _ensure_constraints(self) -> None:
        """Create uniqueness constraints for all node labels."""
        with self._driver.session(database=self._db) as session:
            for label in _LABELS:
                session.run(
                    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) "
                    f"REQUIRE n.uid IS UNIQUE"
                )

    def _run(self, query: str, **params: Any) -> list[dict[str, Any]]:
        """Execute a read Cypher query and return records as dicts."""
        with self._driver.session(database=self._db) as session:
            result = session.run(query, **params)
            return [record.data() for record in result]

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def add_file(self, rf: ResourceFile) -> None:
        """Ingest one parsed ResourceFile into the graph."""
        with self._driver.session(database=self._db) as session:
            session.execute_write(self._add_file_tx, rf)

    @staticmethod
    def _add_file_tx(tx, rf: ResourceFile) -> None:
        fnode = rf.rel_path

        # File node
        tx.run(
            "MERGE (f:File {uid: $uid}) "
            "SET f.node_type = 'file', f.role = $role, "
            "f.platform = $platform, f.doc = $doc",
            uid=fnode, role=rf.role.value,
            platform=rf.platform.value, doc=rf.documentation,
        )

        # Resource imports
        for imp in rf.imports:
            tx.run(
                "MERGE (a:File {uid: $src}) "
                "MERGE (b:File {uid: $tgt}) "
                "MERGE (a)-[:IMPORTS]->(b)",
                src=fnode, tgt=imp,
            )

        # Keywords
        for kw in rf.keywords:
            kw_node = kw.fqn
            tx.run(
                "MERGE (k:Keyword {uid: $uid}) "
                "SET k.node_type = 'keyword', k.doc = $doc, "
                "k.source = $source, k.line = $line",
                uid=kw_node, doc=kw.documentation,
                source=rf.rel_path, line=kw.line_number,
            )
            tx.run(
                "MATCH (f:File {uid: $src}) "
                "MATCH (k:Keyword {uid: $tgt}) "
                "MERGE (f)-[:DEFINES]->(k)",
                src=fnode, tgt=kw_node,
            )
            for called in kw.called_keywords:
                tx.run(
                    "MERGE (a:Keyword {uid: $src}) "
                    "MERGE (b {uid: $tgt}) "
                    "MERGE (a)-[:CALLS]->(b)",
                    src=kw_node, tgt=called,
                )
            for tag in kw.tags:
                tag_node = f"tag:{tag}"
                tx.run(
                    "MERGE (t:Tag {uid: $uid}) SET t.node_type = 'tag'",
                    uid=tag_node,
                )
                tx.run(
                    "MATCH (k:Keyword {uid: $src}) "
                    "MATCH (t:Tag {uid: $tgt}) "
                    "MERGE (k)-[:TAGGED]->(t)",
                    src=kw_node, tgt=tag_node,
                )

        # Test cases
        for tc in rf.test_cases:
            tc_node = tc.fqn
            tx.run(
                "MERGE (t:TestCase {uid: $uid}) "
                "SET t.node_type = 'test_case', t.doc = $doc, "
                "t.source = $source, t.line = $line",
                uid=tc_node, doc=tc.documentation,
                source=rf.rel_path, line=tc.line_number,
            )
            tx.run(
                "MATCH (f:File {uid: $src}) "
                "MATCH (t:TestCase {uid: $tgt}) "
                "MERGE (f)-[:TESTS]->(t)",
                src=fnode, tgt=tc_node,
            )
            for called in tc.called_keywords:
                tx.run(
                    "MERGE (a:TestCase {uid: $src}) "
                    "MERGE (b {uid: $tgt}) "
                    "MERGE (a)-[:CALLS]->(b)",
                    src=tc_node, tgt=called,
                )
            for tag in tc.tags:
                tag_node = f"tag:{tag}"
                tx.run(
                    "MERGE (t:Tag {uid: $uid}) SET t.node_type = 'tag'",
                    uid=tag_node,
                )
                tx.run(
                    "MATCH (tc:TestCase {uid: $src}) "
                    "MATCH (t:Tag {uid: $tgt}) "
                    "MERGE (tc)-[:TAGGED]->(t)",
                    src=tc_node, tgt=tag_node,
                )

        # Variables
        for v in rf.variables:
            var_node = f"var:{v.name}"
            tx.run(
                "MERGE (v:Variable {uid: $uid}) "
                "SET v.node_type = 'variable', v.source = $source, "
                "v.var_type = $var_type",
                uid=var_node, source=rf.rel_path, var_type=v.var_type,
            )
            tx.run(
                "MATCH (f:File {uid: $src}) "
                "MATCH (v:Variable {uid: $tgt}) "
                "MERGE (f)-[:DEFINES]->(v)",
                src=fnode, tgt=var_node,
            )

        # Locator mappings
        for lm in rf.locator_mappings:
            el_node = f"element:{lm.element_name}"
            tx.run(
                "MERGE (e:LocatorElement {uid: $uid}) "
                "SET e.node_type = 'locator_element', "
                "e.ios = $ios, e.android = $android",
                uid=el_node,
                ios=lm.ios_locator or "",
                android=lm.android_locator or "",
            )
            tx.run(
                "MATCH (f:File {uid: $src}) "
                "MATCH (e:LocatorElement {uid: $tgt}) "
                "MERGE (f)-[:MAPS_ELEMENT]->(e)",
                src=fnode, tgt=el_node,
            )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def files_by_role(self, role: str) -> list[str]:
        records = self._run("MATCH (f:File {role: $role}) RETURN f.uid AS uid", role=role)
        return [r["uid"] for r in records]

    def keywords_in_file(self, rel_path: str) -> list[str]:
        records = self._run(
            "MATCH (f:File {uid: $path})-[:DEFINES]->(k:Keyword) RETURN k.uid AS uid",
            path=rel_path,
        )
        return [r["uid"] for r in records]

    def test_cases_in_file(self, rel_path: str) -> list[str]:
        records = self._run(
            "MATCH (f:File {uid: $path})-[:TESTS]->(t:TestCase) RETURN t.uid AS uid",
            path=rel_path,
        )
        return [r["uid"] for r in records]

    def callers_of(self, keyword_fqn: str) -> list[str]:
        """Return nodes that call the given keyword."""
        records = self._run(
            "MATCH (caller)-[:CALLS]->(k {uid: $fqn}) RETURN caller.uid AS uid",
            fqn=keyword_fqn,
        )
        return [r["uid"] for r in records]

    def callees_of(self, node: str) -> list[str]:
        records = self._run(
            "MATCH (n {uid: $node})-[:CALLS]->(callee) RETURN callee.uid AS uid",
            node=node,
        )
        return [r["uid"] for r in records]

    def all_test_cases(self) -> list[str]:
        records = self._run("MATCH (t:TestCase) RETURN t.uid AS uid")
        return [r["uid"] for r in records]

    def all_keywords(self) -> list[str]:
        records = self._run("MATCH (k:Keyword) RETURN k.uid AS uid")
        return [r["uid"] for r in records]

    def tags_of(self, node: str) -> list[str]:
        records = self._run(
            "MATCH (n {uid: $node})-[:TAGGED]->(t:Tag) RETURN t.uid AS uid",
            node=node,
        )
        return [r["uid"].removeprefix("tag:") for r in records]

    def mismatched_po_elements(self) -> list[dict[str, Any]]:
        """Find locator elements that exist in one platform dict but not the other."""
        records = self._run(
            "MATCH (e:LocatorElement) "
            "WHERE (e.ios = '' AND e.android <> '') OR (e.ios <> '' AND e.android = '') "
            "RETURN e.uid AS uid, e.ios AS ios, e.android AS android"
        )
        return [
            {
                "element": r["uid"].removeprefix("element:"),
                "ios": r["ios"] or "MISSING",
                "android": r["android"] or "MISSING",
            }
            for r in records
        ]

    def node_data(self, node: str) -> dict[str, Any]:
        records = self._run(
            "MATCH (n {uid: $node}) RETURN properties(n) AS props",
            node=node,
        )
        if records:
            return dict(records[0]["props"])
        return {}

    # ------------------------------------------------------------------
    # Persistence (no-ops — Neo4j auto-persists)
    # ------------------------------------------------------------------

    def save(self, path: Path) -> None:
        """No-op: Neo4j persists automatically."""
        s = self.summary()
        logger.info(
            "Graph state (%d nodes, %d edges) — Neo4j auto-persisted",
            s.get("total_nodes", 0), s.get("total_edges", 0),
        )

    def load(self, path: Path) -> None:
        """No-op: Neo4j loads state from its own storage."""
        logger.info("Graph load skipped — Neo4j manages its own persistence")

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def summary(self) -> dict[str, int]:
        node_records = self._run(
            "MATCH (n) "
            "RETURN labels(n)[0] AS label, count(n) AS cnt"
        )
        edge_records = self._run("MATCH ()-[r]->() RETURN count(r) AS cnt")

        total_nodes = 0
        types: dict[str, int] = {}
        label_map = {v.lower(): k for k, v in _TYPE_TO_LABEL.items()}
        for r in node_records:
            label = (r["label"] or "unknown").lower()
            node_type = label_map.get(label, label)
            types[node_type] = r["cnt"]
            total_nodes += r["cnt"]

        total_edges = edge_records[0]["cnt"] if edge_records else 0

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            **{f"nodes_{k}": v for k, v in sorted(types.items())},
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        self._driver.close()
