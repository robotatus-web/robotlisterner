"""Tests for the Neo4j graph layer (using mocks)."""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from rf_rag.models import (
    EdgeType,
    FileRole,
    KeywordDef,
    LocatorMapping,
    Platform,
    ResourceFile,
    TestCaseDef,
    VariableDef,
)


class TestRFGraphWithMock:
    """Test RFGraph methods using a mocked Neo4j driver."""

    @pytest.fixture
    def graph(self):
        """Create an RFGraph with a mocked Neo4j driver."""
        with patch("rf_rag.graph.GraphDatabase") as mock_gdb:
            mock_driver = MagicMock()
            mock_session = MagicMock()
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_driver.session.return_value = mock_ctx
            mock_gdb.driver.return_value = mock_driver

            from rf_rag.graph import RFGraph
            g = RFGraph(uri="bolt://mock:7687", auth=("neo4j", "test"))
            yield g, mock_driver, mock_session

    def test_ensure_constraints_called_on_init(self, graph) -> None:
        """Constructor should create uniqueness constraints for all labels."""
        g, driver, session = graph
        # _ensure_constraints should have been called during __init__
        # It creates 6 constraints (one per label)
        constraint_calls = [
            c for c in session.run.call_args_list
            if "CREATE CONSTRAINT" in str(c)
        ]
        assert len(constraint_calls) == 6

    def test_add_file_calls_execute_write(self, graph) -> None:
        """add_file() should use execute_write for transactional safety."""
        g, driver, session = graph
        rf = ResourceFile(
            rel_path="tests/test.robot",
            role=FileRole.ATOMIC_TEST,
            platform=Platform.WEB,
        )
        g.add_file(rf)
        session.execute_write.assert_called_once()

    def test_files_by_role_query(self, graph) -> None:
        """files_by_role() should run the correct Cypher query."""
        g, driver, session = graph
        mock_result = MagicMock()
        mock_record = MagicMock()
        mock_record.data.return_value = {"uid": "tests/login_test.robot"}
        mock_result.__iter__ = MagicMock(return_value=iter([mock_record]))
        session.run.return_value = mock_result

        result = g.files_by_role("ATOMIC_TESTS")
        assert result == ["tests/login_test.robot"]

    def test_callers_of_query(self, graph) -> None:
        """callers_of() should return caller UIDs."""
        g, driver, session = graph
        mock_result = MagicMock()
        mock_records = [MagicMock(), MagicMock()]
        mock_records[0].data.return_value = {"uid": "tc1"}
        mock_records[1].data.return_value = {"uid": "tc2"}
        mock_result.__iter__ = MagicMock(return_value=iter(mock_records))
        session.run.return_value = mock_result

        result = g.callers_of("some_kw.Keyword")
        assert len(result) == 2
        assert "tc1" in result
        assert "tc2" in result

    def test_node_data_returns_properties(self, graph) -> None:
        """node_data() should return node properties as a dict."""
        g, driver, session = graph
        mock_result = MagicMock()
        mock_record = MagicMock()
        mock_record.data.return_value = {
            "props": {"uid": "test.kw", "node_type": "keyword", "source": "test.robot"}
        }
        mock_result.__iter__ = MagicMock(return_value=iter([mock_record]))
        session.run.return_value = mock_result

        result = g.node_data("test.kw")
        assert result["node_type"] == "keyword"
        assert result["source"] == "test.robot"

    def test_node_data_returns_empty_for_missing(self, graph) -> None:
        """node_data() should return {} for missing nodes."""
        g, driver, session = graph
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        session.run.return_value = mock_result

        result = g.node_data("nonexistent")
        assert result == {}

    def test_mismatched_po_elements_query(self, graph) -> None:
        """mismatched_po_elements() should identify elements with one missing locator."""
        g, driver, session = graph
        mock_result = MagicMock()
        mock_record = MagicMock()
        mock_record.data.return_value = {
            "uid": "element:submit_btn",
            "ios": "//XCUIElementTypeButton[@name='Submit']",
            "android": "",
        }
        mock_result.__iter__ = MagicMock(return_value=iter([mock_record]))
        session.run.return_value = mock_result

        result = g.mismatched_po_elements()
        assert len(result) == 1
        assert result[0]["element"] == "submit_btn"
        assert result[0]["android"] == "MISSING"

    def test_tags_of_strips_prefix(self, graph) -> None:
        """tags_of() should strip the 'tag:' prefix."""
        g, driver, session = graph
        mock_result = MagicMock()
        records = [MagicMock(), MagicMock()]
        records[0].data.return_value = {"uid": "tag:web"}
        records[1].data.return_value = {"uid": "tag:smoke"}
        mock_result.__iter__ = MagicMock(return_value=iter(records))
        session.run.return_value = mock_result

        result = g.tags_of("some_kw")
        assert "web" in result
        assert "smoke" in result

    def test_save_is_noop(self, graph, tmp_path) -> None:
        """save() should be a no-op (Neo4j auto-persists)."""
        g, driver, session = graph
        # Make summary() return valid data
        mock_result1 = MagicMock()
        mock_result1.__iter__ = MagicMock(return_value=iter([]))
        mock_result2 = MagicMock()
        mock_result2.__iter__ = MagicMock(return_value=iter([]))
        session.run.return_value = mock_result1
        # Should not raise
        g.save(tmp_path / "graph.json")
        # Should not create the file
        assert not (tmp_path / "graph.json").exists()

    def test_close_closes_driver(self, graph) -> None:
        """close() should close the Neo4j driver."""
        g, driver, session = graph
        g.close()
        driver.close.assert_called_once()

    def test_summary_maps_labels_to_node_types(self, graph) -> None:
        """summary() should map Neo4j labels to internal node_type names."""
        g, driver, session = graph

        # Mock node count query
        mock_node_result = MagicMock()
        node_records = [
            MagicMock(), MagicMock(), MagicMock(),
        ]
        node_records[0].data.return_value = {"label": "File", "cnt": 5}
        node_records[1].data.return_value = {"label": "Keyword", "cnt": 10}
        node_records[2].data.return_value = {"label": "TestCase", "cnt": 3}
        mock_node_result.__iter__ = MagicMock(return_value=iter(node_records))

        # Mock edge count query
        mock_edge_result = MagicMock()
        edge_records = [MagicMock()]
        edge_records[0].data.return_value = {"cnt": 20}
        mock_edge_result.__iter__ = MagicMock(return_value=iter(edge_records))

        session.run.side_effect = [mock_node_result, mock_edge_result]

        result = g.summary()
        assert result["total_nodes"] == 18
        assert result["total_edges"] == 20
        assert result["nodes_file"] == 5
        assert result["nodes_keyword"] == 10
        assert result["nodes_test_case"] == 3
