"""Integration tests for the RAGEngine."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rf_rag.config import RAGConfig
from rf_rag.engine import RAGEngine
from rf_rag.models import FileRole


class TestRAGEngineIngest:
    """Test the full ingest pipeline with mocked Neo4j and in-memory Qdrant."""

    @pytest.fixture
    def engine(self, sample_project_path: Path) -> RAGEngine:
        """Create an engine with mocked Neo4j driver and in-memory Qdrant."""
        cfg = RAGConfig(
            project_root=sample_project_path,
            qdrant_url=None,
            qdrant_path=None,
        )

        with patch("rf_rag.graph.GraphDatabase") as mock_gdb:
            mock_driver = MagicMock()
            mock_session = MagicMock()
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_driver.session.return_value = mock_ctx
            mock_gdb.driver.return_value = mock_driver

            engine = RAGEngine(cfg)
            yield engine

    def test_ingest_returns_stats(self, engine: RAGEngine) -> None:
        """ingest() should return summary statistics."""
        stats = engine.ingest()
        assert "files_crawled" in stats
        assert "keywords" in stats
        assert "test_cases" in stats
        assert "vectors_indexed" in stats

    def test_ingest_finds_all_files(self, engine: RAGEngine) -> None:
        """ingest() should crawl all 8 RF files in the sample project."""
        stats = engine.ingest()
        assert stats["files_crawled"] == 8

    def test_ingest_indexes_keywords(self, engine: RAGEngine) -> None:
        """ingest() should find keywords across all resource files."""
        stats = engine.ingest()
        assert stats["keywords"] > 0

    def test_ingest_indexes_test_cases(self, engine: RAGEngine) -> None:
        """ingest() should find test cases in .robot files."""
        stats = engine.ingest()
        assert stats["test_cases"] > 0

    def test_ingest_indexes_vectors(self, engine: RAGEngine) -> None:
        """ingest() should index vectors into Qdrant."""
        stats = engine.ingest()
        assert stats["vectors_indexed"] > 0

    def test_ingest_populates_file_map(self, engine: RAGEngine) -> None:
        """After ingest(), file_map should contain all crawled files."""
        engine.ingest()
        assert len(engine.file_map) == 8

    def test_ingest_assigns_correct_roles(self, engine: RAGEngine) -> None:
        """After ingest(), file_map should have correct role assignments."""
        engine.ingest()
        roles = {rf.role for rf in engine.file_map.values()}
        assert FileRole.ATOMIC_TEST in roles
        assert FileRole.E2E_TEST in roles
        assert FileRole.FLOW in roles
        assert FileRole.PAGE_OBJECT in roles
        assert FileRole.API in roles

    def test_query_requires_ingest(self, engine: RAGEngine) -> None:
        """query() should raise if ingest() hasn't been called."""
        with pytest.raises(RuntimeError, match="ingest"):
            engine.query("login")

    def test_query_after_ingest(self, engine: RAGEngine) -> None:
        """query() should work after ingest()."""
        engine.ingest()
        result = engine.query("login credentials")
        assert result.count > 0

    def test_inventory_keywords_after_ingest(self, engine: RAGEngine) -> None:
        """inventory_keywords() should list all keywords."""
        engine.ingest()
        result = engine.inventory_keywords()
        assert result.count > 0

    def test_inventory_tests_after_ingest(self, engine: RAGEngine) -> None:
        """inventory_tests() should list all test cases."""
        engine.ingest()
        result = engine.inventory_tests()
        assert result.count > 0

    def test_vector_store_has_data(self, engine: RAGEngine) -> None:
        """After ingest(), the vector store should have indexed items."""
        engine.ingest()
        assert engine.vector_store.count() > 0

    def test_smoke_after_ingest(self, engine: RAGEngine) -> None:
        """smoke() should return candidates after ingest()."""
        engine.ingest()
        candidates = engine.smoke(n=3)
        assert len(candidates) > 0

    def test_close_method_exists(self, engine: RAGEngine) -> None:
        """Engine should have a close() method."""
        assert hasattr(engine, "close")
        engine.close()  # Should not raise
