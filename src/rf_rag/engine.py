"""Central orchestration engine — ties together all RAG components."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from rf_rag.config import RAGConfig
from rf_rag.crawler import crawl
from rf_rag.graph import RFGraph
from rf_rag.models import ResourceFile
from rf_rag.modules.codegen import DRYCodeGenerator, GeneratedCode
from rf_rag.modules.query import QueryEngine, QueryResult
from rf_rag.modules.redundancy import RedundancyDetector, RedundancyReport
from rf_rag.modules.smoke import SmokeCandidate, farthest_point_sampling
from rf_rag.parser import parse_file
from rf_rag.resolver import ResourceResolver
from rf_rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)


class RAGEngine:
    """Main entry point for the RF-RAG system.

    Lifecycle:
        engine = RAGEngine(cfg)
        engine.ingest()          # crawl → parse → index
        engine.redundancy()      # Module 1
        engine.smoke(n=20)       # Module 2
        engine.query(...)        # Module 3
        engine.generate(...)     # Module 4
    """

    def __init__(self, cfg: RAGConfig) -> None:
        self.cfg = cfg
        self.graph = RFGraph()
        self.vector_store = VectorStore(cfg)
        self.file_map: dict[str, ResourceFile] = {}
        self._resolver: ResourceResolver | None = None
        self._query_engine: QueryEngine | None = None
        self._codegen: DRYCodeGenerator | None = None

    # ------------------------------------------------------------------
    # Ingestion pipeline
    # ------------------------------------------------------------------

    def ingest(self) -> dict[str, int]:
        """Run the full ingestion pipeline: crawl → parse → graph + vector index.

        Returns summary statistics.
        """
        project_root = self.cfg.project_root.resolve()

        files_crawled = 0
        keywords_total = 0
        tests_total = 0
        vectors_total = 0

        for filepath in crawl(project_root):
            try:
                rf = parse_file(filepath, self.cfg)
            except Exception:
                logger.exception("Failed to parse %s", filepath)
                continue

            rel = rf.rel_path
            self.file_map[rel] = rf

            # Graph
            self.graph.add_file(rf)

            # Vector store
            n_indexed = self.vector_store.index_file(rf)
            vectors_total += n_indexed

            files_crawled += 1
            keywords_total += len(rf.keywords)
            tests_total += len(rf.test_cases)

        # Initialise resolver after all files are parsed
        self._resolver = ResourceResolver(self.file_map, project_root)
        self._query_engine = QueryEngine(
            self.graph, self.vector_store, self.file_map, self._resolver,
        )
        self._codegen = DRYCodeGenerator(
            self.graph, self.vector_store, self.file_map, self._resolver,
        )

        # Persist graph
        graph_path = self.cfg.effective_data_dir() / "graph.json"
        self.graph.save(graph_path)

        stats = {
            "files_crawled": files_crawled,
            "keywords": keywords_total,
            "test_cases": tests_total,
            "vectors_indexed": vectors_total,
            **self.graph.summary(),
        }
        logger.info("Ingestion complete: %s", stats)
        return stats

    # ------------------------------------------------------------------
    # Module 1: Redundancy
    # ------------------------------------------------------------------

    def redundancy(self) -> RedundancyReport:
        detector = RedundancyDetector(
            self.graph, self.vector_store, self.file_map,
            similarity_threshold=self.cfg.similarity_threshold,
        )
        return detector.detect()

    # ------------------------------------------------------------------
    # Module 2: Smoke selection
    # ------------------------------------------------------------------

    def smoke(self, n: int | None = None) -> list[SmokeCandidate]:
        count = n or self.cfg.smoke_test_count
        return farthest_point_sampling(self.vector_store, n=count)

    # ------------------------------------------------------------------
    # Module 3: Query
    # ------------------------------------------------------------------

    def query(self, text: str, n: int = 10) -> QueryResult:
        if self._query_engine is None:
            raise RuntimeError("Run ingest() first.")
        return self._query_engine.semantic_search(text, n=n)

    def inventory_keywords(self) -> QueryResult:
        if self._query_engine is None:
            raise RuntimeError("Run ingest() first.")
        return self._query_engine.keyword_inventory()

    def inventory_tests(self) -> QueryResult:
        if self._query_engine is None:
            raise RuntimeError("Run ingest() first.")
        return self._query_engine.test_inventory()

    def graphql_coverage(self) -> QueryResult:
        if self._query_engine is None:
            raise RuntimeError("Run ingest() first.")
        return self._query_engine.graphql_mutations_without_sit()

    def po_mismatches(self) -> QueryResult:
        if self._query_engine is None:
            raise RuntimeError("Run ingest() first.")
        return self._query_engine.mismatched_po_keys()

    def effective_scope(self, rel_path: str) -> QueryResult:
        if self._query_engine is None:
            raise RuntimeError("Run ingest() first.")
        return self._query_engine.effective_scope(rel_path)

    # ------------------------------------------------------------------
    # Module 4: Code generation
    # ------------------------------------------------------------------

    def generate(
        self,
        description: str,
        target_path: str,
        tags: list[str] | None = None,
        platform: str = "web",
    ) -> GeneratedCode:
        if self._codegen is None:
            raise RuntimeError("Run ingest() first.")
        return self._codegen.generate_test_suite(
            description=description,
            target_path=target_path,
            tags=tags,
            platform=platform,
        )
