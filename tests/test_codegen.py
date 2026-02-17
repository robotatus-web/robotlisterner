"""Tests for the code generation module."""

from __future__ import annotations

from pathlib import PurePosixPath
from unittest.mock import MagicMock

import pytest

from rf_rag.models import FileRole, Platform, ResourceFile
from rf_rag.modules.codegen import DRYCodeGenerator, GeneratedCode, _relative_path
from rf_rag.resolver import ResourceResolver


class TestRelativePath:
    """Test the _relative_path() utility function."""

    def test_same_directory(self) -> None:
        result = _relative_path("tests/a.robot", "tests/common.resource")
        assert result == "common.resource"

    def test_sibling_directory(self) -> None:
        result = _relative_path("tests/login/a.robot", "resources/common.resource")
        assert result == "../../resources/common.resource"

    def test_nested_to_parent(self) -> None:
        result = _relative_path("tests/migration/v2/a.robot", "resources/platform/common.resource")
        assert result == "../../../resources/platform/common.resource"

    def test_root_to_nested(self) -> None:
        result = _relative_path("a.robot", "resources/web/flow/login_flow.resource")
        assert result == "resources/web/flow/login_flow.resource"

    def test_same_file(self) -> None:
        result = _relative_path("a.robot", "a.robot")
        assert result == "a.robot"


class TestDRYCodeGenerator:
    @pytest.fixture
    def mock_graph(self):
        return MagicMock()

    @pytest.fixture
    def mock_vs(self):
        vs = MagicMock()
        vs.search.return_value = [
            {
                "document": "Performs login with valid credentials",
                "metadata": {
                    "type": "keyword",
                    "fqn": "login_flow.Login With Valid Credentials",
                    "name": "Login With Valid Credentials",
                    "source": "resources/web/flow/login_flow.resource",
                    "role": FileRole.FLOW.value,
                },
                "distance": 0.1,
            },
            {
                "document": "Enters username and password",
                "metadata": {
                    "type": "keyword",
                    "fqn": "login_page.Input Login Credentials",
                    "name": "Input Login Credentials",
                    "source": "resources/web/po/login_page.resource",
                    "role": FileRole.PAGE_OBJECT.value,
                },
                "distance": 0.2,
            },
        ]
        return vs

    @pytest.fixture
    def file_map(self) -> dict[str, ResourceFile]:
        return {
            "resources/platform/common.resource": ResourceFile(
                rel_path="resources/platform/common.resource",
                role=FileRole.KNOWLEDGE_BASE,
                platform=Platform.COMMON,
                imports=[
                    "resources/web/flow/login_flow.resource",
                    "resources/web/po/login_page.resource",
                ],
            ),
            "resources/web/flow/login_flow.resource": ResourceFile(
                rel_path="resources/web/flow/login_flow.resource",
                role=FileRole.FLOW,
                platform=Platform.WEB,
                imports=["resources/web/po/login_page.resource"],
            ),
            "resources/web/po/login_page.resource": ResourceFile(
                rel_path="resources/web/po/login_page.resource",
                role=FileRole.PAGE_OBJECT,
                platform=Platform.WEB,
            ),
        }

    @pytest.fixture
    def resolver(self, file_map, tmp_path):
        return ResourceResolver(file_map, tmp_path)

    @pytest.fixture
    def codegen(self, mock_graph, mock_vs, file_map, resolver):
        return DRYCodeGenerator(mock_graph, mock_vs, file_map, resolver)

    def test_generate_test_suite_returns_code(self, codegen) -> None:
        """generate_test_suite() should return a GeneratedCode with valid content."""
        result = codegen.generate_test_suite(
            description="Verify user login flow",
            target_path="tests/new_test.robot",
            tags=["web", "smoke"],
            platform="web",
        )
        assert isinstance(result, GeneratedCode)
        assert result.filename == "tests/new_test.robot"
        assert "*** Settings ***" in result.content
        assert "*** Test Cases ***" in result.content
        assert "*** Keywords ***" in result.content

    def test_generated_code_includes_reused_keywords(self, codegen) -> None:
        """Generated code should call reused keywords."""
        result = codegen.generate_test_suite(
            description="Verify login",
            target_path="tests/new_test.robot",
        )
        assert len(result.reused_keywords) > 0
        assert any("Login" in kw for kw in result.reused_keywords)

    def test_generated_code_has_import(self, codegen) -> None:
        """Generated code should include a Resource import."""
        result = codegen.generate_test_suite(
            description="Verify login",
            target_path="tests/new_test.robot",
        )
        assert "Resource" in result.content
        assert len(result.import_chain) > 0

    def test_generated_code_has_tags(self, codegen) -> None:
        """Generated code should include specified tags."""
        result = codegen.generate_test_suite(
            description="Verify login",
            target_path="tests/new_test.robot",
            tags=["web", "regression"],
        )
        assert "web" in result.content
        assert "regression" in result.content

    def test_generated_code_has_base_data_creation(self, codegen) -> None:
        """Generated code should include Base Data Creation keyword."""
        result = codegen.generate_test_suite(
            description="Verify login",
            target_path="tests/new_test.robot",
        )
        assert "Base Data Creation" in result.content

    def test_generated_code_has_teardown(self, codegen) -> None:
        """Generated code should include a teardown."""
        result = codegen.generate_test_suite(
            description="Verify login",
            target_path="tests/new_test.robot",
        )
        assert "Teardown" in result.content
