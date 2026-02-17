"""Tests for the FPS smoke test selection module."""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

from rf_rag.modules.smoke import SmokeCandidate, farthest_point_sampling


class TestFarthestPointSampling:
    @pytest.fixture
    def mock_vs(self):
        return MagicMock()

    def test_returns_requested_count(self, mock_vs) -> None:
        """FPS should return exactly n candidates when enough test cases exist."""
        # Create 10 test case embeddings (384-dim)
        rng = np.random.RandomState(42)
        embeddings = {f"id_{i}": rng.randn(384).tolist() for i in range(10)}
        mock_vs.get_all_embeddings.return_value = embeddings
        mock_vs.get_metadata.side_effect = lambda doc_id: {
            "fqn": f"test.{doc_id}",
            "source": "tests/test.robot",
            "tags": "web,smoke",
        }

        result = farthest_point_sampling(mock_vs, n=5)
        assert len(result) == 5

    def test_returns_all_when_fewer_than_n(self, mock_vs) -> None:
        """FPS should return all if fewer test cases than n."""
        rng = np.random.RandomState(42)
        embeddings = {f"id_{i}": rng.randn(384).tolist() for i in range(3)}
        mock_vs.get_all_embeddings.return_value = embeddings
        mock_vs.get_metadata.side_effect = lambda doc_id: {
            "fqn": f"test.{doc_id}",
            "source": "tests/test.robot",
            "tags": "web",
        }

        result = farthest_point_sampling(mock_vs, n=10)
        assert len(result) == 3

    def test_no_duplicate_selections(self, mock_vs) -> None:
        """FPS should not select the same test case twice."""
        rng = np.random.RandomState(42)
        embeddings = {f"id_{i}": rng.randn(384).tolist() for i in range(10)}
        mock_vs.get_all_embeddings.return_value = embeddings
        mock_vs.get_metadata.side_effect = lambda doc_id: {
            "fqn": f"test.{doc_id}",
            "source": "tests/test.robot",
            "tags": "",
        }

        result = farthest_point_sampling(mock_vs, n=10)
        fqns = [c.fqn for c in result]
        assert len(fqns) == len(set(fqns))

    def test_empty_embeddings(self, mock_vs) -> None:
        """FPS should return empty list when no test case embeddings exist."""
        mock_vs.get_all_embeddings.return_value = {}
        result = farthest_point_sampling(mock_vs, n=5)
        assert result == []

    def test_single_test_case(self, mock_vs) -> None:
        """FPS with one test case should return just that one."""
        embeddings = {"only_one": [1.0] * 384}
        mock_vs.get_all_embeddings.return_value = embeddings
        mock_vs.get_metadata.return_value = {
            "fqn": "test.Only Test",
            "source": "tests/test.robot",
            "tags": "web",
        }

        result = farthest_point_sampling(mock_vs, n=5)
        assert len(result) == 1
        assert result[0].fqn == "test.Only Test"

    def test_result_has_correct_fields(self, mock_vs) -> None:
        """Each SmokeCandidate should have fqn, source, tags, distance_score."""
        rng = np.random.RandomState(42)
        embeddings = {f"id_{i}": rng.randn(384).tolist() for i in range(5)}
        mock_vs.get_all_embeddings.return_value = embeddings
        mock_vs.get_metadata.side_effect = lambda doc_id: {
            "fqn": f"test.{doc_id}",
            "source": "tests/test.robot",
            "tags": "web,smoke",
        }

        result = farthest_point_sampling(mock_vs, n=3)
        for candidate in result:
            assert isinstance(candidate, SmokeCandidate)
            assert candidate.fqn != ""
            assert candidate.source != ""
            assert isinstance(candidate.tags, list)
            assert isinstance(candidate.distance_score, float)

    def test_tags_parsed_from_csv(self, mock_vs) -> None:
        """Tags should be parsed from comma-separated metadata."""
        embeddings = {"id_0": [1.0] * 384}
        mock_vs.get_all_embeddings.return_value = embeddings
        mock_vs.get_metadata.return_value = {
            "fqn": "test.Tagged",
            "source": "tests/test.robot",
            "tags": "web,smoke,e2e",
        }

        result = farthest_point_sampling(mock_vs, n=1)
        assert "web" in result[0].tags
        assert "smoke" in result[0].tags
        assert "e2e" in result[0].tags
