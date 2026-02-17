"""Tests for the Qdrant vector store layer (using in-memory Qdrant)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from rf_rag.config import RAGConfig
from rf_rag.models import (
    FileRole,
    KeywordDef,
    Platform,
    ResourceFile,
    TestCaseDef,
)
from rf_rag.vectorstore import VectorStore, _build_embedding_text, _doc_id


@pytest.fixture
def vs_config(tmp_path: Path) -> RAGConfig:
    """Config for vector store tests with in-memory Qdrant."""
    return RAGConfig(
        project_root=tmp_path,
        qdrant_url=None,
        qdrant_path=None,
        embedding_dim=384,
    )


@pytest.fixture
def vector_store(vs_config: RAGConfig) -> VectorStore:
    """Create a VectorStore with in-memory Qdrant."""
    return VectorStore(vs_config)


@pytest.fixture
def indexed_store(vector_store: VectorStore, sample_resource_file: ResourceFile,
                  sample_test_file: ResourceFile) -> VectorStore:
    """VectorStore with sample data already indexed."""
    vector_store.index_file(sample_resource_file)
    vector_store.index_file(sample_test_file)
    return vector_store


class TestBuildEmbeddingText:
    def test_doc_priority(self) -> None:
        result = _build_embedding_text("The documentation", "body text", "Name")
        assert result.startswith("The documentation")

    def test_name_only_fallback(self) -> None:
        result = _build_embedding_text("", "", "MyKeyword")
        assert result == "MyKeyword"

    def test_all_parts(self) -> None:
        result = _build_embedding_text("doc", "body", "name")
        assert "doc" in result
        assert "body" in result
        assert "name" in result


class TestDocId:
    def test_deterministic(self) -> None:
        assert _doc_id("test") == _doc_id("test")

    def test_different_inputs_different_ids(self) -> None:
        assert _doc_id("a") != _doc_id("b")

    def test_uuid_format(self) -> None:
        """_doc_id should return a valid UUID string."""
        import uuid
        result = _doc_id("test")
        uuid.UUID(result)  # should not raise


class TestVectorStoreIndexing:
    def test_index_file_returns_count(self, vector_store: VectorStore,
                                      sample_resource_file: ResourceFile) -> None:
        """index_file() should return the number of items indexed."""
        count = vector_store.index_file(sample_resource_file)
        # 1 keyword + file doc (if non-empty)
        assert count >= 1

    def test_count_after_indexing(self, vector_store: VectorStore,
                                  sample_resource_file: ResourceFile) -> None:
        """count() should reflect indexed items."""
        assert vector_store.count() == 0
        vector_store.index_file(sample_resource_file)
        assert vector_store.count() > 0

    def test_index_file_with_test_cases(self, vector_store: VectorStore,
                                         sample_test_file: ResourceFile) -> None:
        """Indexing a file with test cases should include them."""
        count = vector_store.index_file(sample_test_file)
        # 1 keyword + 1 test_case + file doc
        assert count >= 2

    def test_upsert_idempotent(self, vector_store: VectorStore,
                                sample_resource_file: ResourceFile) -> None:
        """Indexing the same file twice should not duplicate entries."""
        vector_store.index_file(sample_resource_file)
        count1 = vector_store.count()
        vector_store.index_file(sample_resource_file)
        count2 = vector_store.count()
        assert count1 == count2


class TestVectorStoreSearch:
    def test_search_returns_results(self, indexed_store: VectorStore) -> None:
        """search() should return matching items."""
        results = indexed_store.search("login credentials")
        assert len(results) > 0

    def test_search_result_structure(self, indexed_store: VectorStore) -> None:
        """Each search result should have id, document, metadata, distance."""
        results = indexed_store.search("login")
        for r in results:
            assert "id" in r
            assert "document" in r
            assert "metadata" in r
            assert "distance" in r

    def test_search_with_filter(self, indexed_store: VectorStore) -> None:
        """search() with where filter should only return matching types."""
        results = indexed_store.search("login", where={"type": "keyword"})
        for r in results:
            assert r["metadata"]["type"] == "keyword"

    def test_search_n_results_limit(self, indexed_store: VectorStore) -> None:
        """search() should respect n_results limit."""
        results = indexed_store.search("login", n_results=1)
        assert len(results) <= 1


class TestVectorStoreEmbeddings:
    def test_get_all_embeddings(self, indexed_store: VectorStore) -> None:
        """get_all_embeddings() should return {id: vector} dict."""
        embeddings = indexed_store.get_all_embeddings()
        assert len(embeddings) > 0
        for uid, vec in embeddings.items():
            assert isinstance(vec, list)
            assert len(vec) == 384

    def test_get_all_embeddings_with_filter(self, indexed_store: VectorStore) -> None:
        """get_all_embeddings() with filter should only return matching items."""
        kw_embeddings = indexed_store.get_all_embeddings(where={"type": "keyword"})
        tc_embeddings = indexed_store.get_all_embeddings(where={"type": "test_case"})
        # Should not be the same set
        assert set(kw_embeddings.keys()) != set(tc_embeddings.keys())


class TestVectorStoreMetadata:
    def test_get_metadata(self, indexed_store: VectorStore) -> None:
        """get_metadata() should return payload for a known point."""
        # Get an ID from get_all_embeddings
        embeddings = indexed_store.get_all_embeddings()
        some_id = next(iter(embeddings))
        meta = indexed_store.get_metadata(some_id)
        assert "type" in meta
        assert "fqn" in meta

    def test_get_metadata_missing_id(self, indexed_store: VectorStore) -> None:
        """get_metadata() should return {} for non-existent ID."""
        meta = indexed_store.get_metadata("nonexistent_id_12345")
        assert meta == {}

    def test_metadata_excludes_document(self, indexed_store: VectorStore) -> None:
        """get_metadata() should not include _document in payload."""
        embeddings = indexed_store.get_all_embeddings()
        some_id = next(iter(embeddings))
        meta = indexed_store.get_metadata(some_id)
        assert "_document" not in meta


class TestVectorStoreClear:
    def test_clear_removes_all(self, indexed_store: VectorStore) -> None:
        """clear() should remove all documents."""
        assert indexed_store.count() > 0
        indexed_store.clear()
        assert indexed_store.count() == 0

    def test_clear_allows_reindex(self, indexed_store: VectorStore,
                                   sample_resource_file: ResourceFile) -> None:
        """After clear(), should be able to index again."""
        indexed_store.clear()
        indexed_store.index_file(sample_resource_file)
        assert indexed_store.count() > 0
