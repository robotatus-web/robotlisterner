"""Tests for the redundancy detection module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from rf_rag.config import RAGConfig
from rf_rag.models import FileRole, Platform, ResourceFile
from rf_rag.modules.redundancy import RedundancyDetector, RedundancyReport, _cosine_similarity


class TestCosineSimilarity:
    def test_identical_vectors(self) -> None:
        a = [1.0, 0.0, 0.0]
        b = [1.0, 0.0, 0.0]
        assert abs(_cosine_similarity(a, b) - 1.0) < 1e-6

    def test_orthogonal_vectors(self) -> None:
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert abs(_cosine_similarity(a, b)) < 1e-6

    def test_opposite_vectors(self) -> None:
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert abs(_cosine_similarity(a, b) + 1.0) < 1e-6

    def test_zero_vector(self) -> None:
        a = [0.0, 0.0]
        b = [1.0, 0.0]
        assert _cosine_similarity(a, b) == 0.0


class TestRedundancyDetector:
    @pytest.fixture
    def mock_graph(self):
        return MagicMock()

    @pytest.fixture
    def mock_vs(self):
        vs = MagicMock()
        return vs

    @pytest.fixture
    def file_map(self) -> dict[str, ResourceFile]:
        return {
            "tests/login_test.robot": ResourceFile(
                rel_path="tests/login_test.robot",
                role=FileRole.ATOMIC_TEST,
                platform=Platform.WEB,
            ),
            "SIT/e2e_flow.robot": ResourceFile(
                rel_path="SIT/e2e_flow.robot",
                role=FileRole.E2E_TEST,
                platform=Platform.WEB,
            ),
            "tests/migration/v2/mig.robot": ResourceFile(
                rel_path="tests/migration/v2/mig.robot",
                role=FileRole.MIGRATION_TEST,
                platform=Platform.WEB,
            ),
        }

    def test_horizontal_detects_duplicate_setup(
        self, mock_graph, mock_vs, file_map
    ) -> None:
        """Horizontal detection should flag similar setup keywords across suites."""
        # Two setup keywords from different files with identical embeddings
        vec = [1.0] * 10
        mock_vs.get_all_embeddings.return_value = {
            "id_setup_a": vec,
            "id_setup_b": vec,
            "id_other": [0.0] * 10,
        }
        mock_vs.get_metadata.side_effect = lambda doc_id: {
            "id_setup_a": {"fqn": "fileA.Base Data Creation", "name": "Base Data Creation",
                           "source": "tests/a.robot"},
            "id_setup_b": {"fqn": "fileB.Base Data Creation", "name": "Base Data Creation",
                           "source": "tests/b.robot"},
            "id_other": {"fqn": "fileA.Other KW", "name": "Other KW", "source": "tests/a.robot"},
        }[doc_id]

        detector = RedundancyDetector(mock_graph, mock_vs, file_map, similarity_threshold=0.90)
        report = detector.detect()

        horizontal_hits = [h for h in report.hits if h.kind == "horizontal"]
        assert len(horizontal_hits) >= 1
        assert horizontal_hits[0].similarity >= 0.90

    def test_vertical_detects_sit_coverage(
        self, mock_graph, mock_vs, file_map
    ) -> None:
        """Vertical detection should flag atomic tests covered by SIT."""
        vec = [1.0] * 10
        mock_vs.get_all_embeddings.return_value = {
            "id_atomic": vec,
            "id_sit": vec,
        }
        mock_vs.get_metadata.side_effect = lambda doc_id: {
            "id_atomic": {"fqn": "login_test.Login Test", "role": FileRole.ATOMIC_TEST.value},
            "id_sit": {"fqn": "e2e_flow.Login E2E", "role": FileRole.E2E_TEST.value},
        }[doc_id]

        detector = RedundancyDetector(mock_graph, mock_vs, file_map, similarity_threshold=0.90)
        report = detector.detect()

        vertical_hits = [h for h in report.hits if h.kind == "vertical"]
        assert len(vertical_hits) >= 1

    def test_migration_sync_detects_coverage(
        self, mock_graph, mock_vs, file_map
    ) -> None:
        """Migration sync should flag migration tests covered by atomic/SIT tests."""
        vec = [1.0] * 10
        mock_vs.get_all_embeddings.return_value = {
            "id_mig": vec,
            "id_atomic": vec,
        }
        mock_vs.get_metadata.side_effect = lambda doc_id: {
            "id_mig": {"fqn": "mig.V2 Login", "role": FileRole.MIGRATION_TEST.value},
            "id_atomic": {"fqn": "login_test.Login", "role": FileRole.ATOMIC_TEST.value},
        }[doc_id]

        detector = RedundancyDetector(mock_graph, mock_vs, file_map, similarity_threshold=0.90)
        report = detector.detect()

        mig_hits = [h for h in report.hits if h.kind == "migration_sync"]
        assert len(mig_hits) >= 1

    def test_no_false_positives_below_threshold(
        self, mock_graph, mock_vs, file_map
    ) -> None:
        """Dissimilar keywords should not be flagged."""
        mock_vs.get_all_embeddings.return_value = {
            "id_a": [1.0, 0.0, 0.0],
            "id_b": [0.0, 1.0, 0.0],
        }
        mock_vs.get_metadata.side_effect = lambda doc_id: {
            "id_a": {"fqn": "a.Setup", "name": "Setup", "source": "tests/a.robot"},
            "id_b": {"fqn": "b.Teardown", "name": "Setup", "source": "tests/b.robot"},
        }[doc_id]

        detector = RedundancyDetector(mock_graph, mock_vs, file_map, similarity_threshold=0.90)
        report = detector.detect()
        assert len(report.hits) == 0

    def test_report_summary(self) -> None:
        """RedundancyReport.summary() should aggregate by kind."""
        from rf_rag.modules.redundancy import RedundancyHit
        report = RedundancyReport(hits=[
            RedundancyHit("horizontal", "a", "b", 0.95, "rec"),
            RedundancyHit("horizontal", "c", "d", 0.92, "rec"),
            RedundancyHit("vertical", "e", "f", 0.91, "rec"),
        ])
        summary = report.summary()
        assert summary["total"] == 3
        assert summary["by_kind"]["horizontal"] == 2
        assert summary["by_kind"]["vertical"] == 1
