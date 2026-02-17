"""Tests for the Robot Framework file parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from rf_rag.config import RAGConfig
from rf_rag.models import FileRole, Platform
from rf_rag.parser import parse_file


@pytest.fixture
def cfg(sample_project_path: Path) -> RAGConfig:
    return RAGConfig(project_root=sample_project_path)


class TestParseFile:
    """Test parse_file() with actual RF fixture files."""

    def test_parse_test_file_role(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Tests under tests/ should be assigned ATOMIC_TEST role."""
        filepath = sample_project_path / "tests" / "login_test.robot"
        rf = parse_file(filepath, cfg)
        assert rf.role == FileRole.ATOMIC_TEST

    def test_parse_sit_file_role(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Files under SIT/ should be assigned E2E_TEST role."""
        filepath = sample_project_path / "SIT" / "e2e_login_flow.robot"
        rf = parse_file(filepath, cfg)
        assert rf.role == FileRole.E2E_TEST

    def test_parse_migration_test_role(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Files under tests/migration/ should be MIGRATION_TEST."""
        filepath = sample_project_path / "tests" / "migration" / "v2" / "login_migration_test.robot"
        rf = parse_file(filepath, cfg)
        assert rf.role == FileRole.MIGRATION_TEST

    def test_parse_po_role(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Files under resources/**/po/ should be PAGE_OBJECT."""
        filepath = sample_project_path / "resources" / "web" / "po" / "login_page.resource"
        rf = parse_file(filepath, cfg)
        assert rf.role == FileRole.PAGE_OBJECT

    def test_parse_flow_role(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Files under resources/**/flow/ should be FLOW."""
        filepath = sample_project_path / "resources" / "web" / "flow" / "login_flow.resource"
        rf = parse_file(filepath, cfg)
        assert rf.role == FileRole.FLOW

    def test_parse_api_role(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Files under resources/**/api/ should be API."""
        filepath = sample_project_path / "resources" / "be" / "api" / "graphql.resource"
        rf = parse_file(filepath, cfg)
        assert rf.role == FileRole.API

    def test_parse_data_layer_role(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Files under data/ should be DATA_LAYER."""
        filepath = sample_project_path / "data" / "GlobalVariables.resource"
        rf = parse_file(filepath, cfg)
        assert rf.role == FileRole.DATA_LAYER

    def test_platform_assignment_web(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Files under resources/web/ should get WEB platform."""
        filepath = sample_project_path / "resources" / "web" / "flow" / "login_flow.resource"
        rf = parse_file(filepath, cfg)
        assert rf.platform == Platform.WEB

    def test_platform_assignment_be(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Files under resources/be/ should get BE platform."""
        filepath = sample_project_path / "resources" / "be" / "api" / "graphql.resource"
        rf = parse_file(filepath, cfg)
        assert rf.platform == Platform.BE

    def test_keywords_extracted(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Parser should extract keywords from resource files."""
        filepath = sample_project_path / "resources" / "web" / "flow" / "login_flow.resource"
        rf = parse_file(filepath, cfg)
        kw_names = [kw.name for kw in rf.keywords]
        assert "Login With Valid Credentials" in kw_names
        assert "Login With Custom Credentials" in kw_names
        assert "Logout From Application" in kw_names

    def test_test_cases_extracted(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Parser should extract test cases from .robot files."""
        filepath = sample_project_path / "tests" / "login_test.robot"
        rf = parse_file(filepath, cfg)
        tc_names = [tc.name for tc in rf.test_cases]
        assert "Valid Login With Default Credentials" in tc_names
        assert "Invalid Login Shows Error Message" in tc_names

    def test_keyword_fqn_format(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Keyword FQN should be ResourceName.KeywordName."""
        filepath = sample_project_path / "resources" / "web" / "flow" / "login_flow.resource"
        rf = parse_file(filepath, cfg)
        fqns = [kw.fqn for kw in rf.keywords]
        assert "login_flow.Login With Valid Credentials" in fqns

    def test_keyword_documentation(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Keyword documentation should be extracted."""
        filepath = sample_project_path / "resources" / "web" / "flow" / "login_flow.resource"
        rf = parse_file(filepath, cfg)
        kw = next(kw for kw in rf.keywords if kw.name == "Login With Valid Credentials")
        assert "login" in kw.documentation.lower()

    def test_keyword_tags_extracted(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Keyword tags should be extracted."""
        filepath = sample_project_path / "resources" / "web" / "flow" / "login_flow.resource"
        rf = parse_file(filepath, cfg)
        kw = next(kw for kw in rf.keywords if kw.name == "Login With Valid Credentials")
        assert "web" in kw.tags
        assert "smoke" in kw.tags

    def test_test_case_tags_extracted(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Test case tags should be extracted."""
        filepath = sample_project_path / "tests" / "login_test.robot"
        rf = parse_file(filepath, cfg)
        tc = next(tc for tc in rf.test_cases if tc.name == "Valid Login With Default Credentials")
        assert "web" in tc.tags
        assert "smoke" in tc.tags
        assert "login" in tc.tags

    def test_resource_imports_extracted(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Parser should extract resource imports."""
        filepath = sample_project_path / "resources" / "platform" / "common.resource"
        rf = parse_file(filepath, cfg)
        assert len(rf.imports) >= 3

    def test_variables_extracted(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Parser should extract variables from the Variables section."""
        filepath = sample_project_path / "data" / "GlobalVariables.resource"
        rf = parse_file(filepath, cfg)
        var_names = [v.name for v in rf.variables]
        assert any("BASE_URL" in n for n in var_names)
        assert any("TIMEOUT" in n for n in var_names)

    def test_credential_redaction(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Variables with sensitive names should be redacted."""
        filepath = sample_project_path / "data" / "GlobalVariables.resource"
        rf = parse_file(filepath, cfg)
        pw_var = next((v for v in rf.variables if "PASSWORD" in v.name.upper()), None)
        assert pw_var is not None
        assert pw_var.value_repr == "***REDACTED***"

    def test_locator_mappings_extracted(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Parser should extract &{IOS} and &{ANDROID} dict locator mappings."""
        filepath = sample_project_path / "resources" / "web" / "po" / "login_page.resource"
        rf = parse_file(filepath, cfg)
        element_names = [lm.element_name for lm in rf.locator_mappings]
        assert "login_btn" in element_names
        assert "username_field" in element_names

    def test_locator_mismatch_detected(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """submit_btn exists only in &{IOS} — should appear with no Android locator."""
        filepath = sample_project_path / "resources" / "web" / "po" / "login_page.resource"
        rf = parse_file(filepath, cfg)
        submit = next((lm for lm in rf.locator_mappings if lm.element_name == "submit_btn"), None)
        assert submit is not None
        assert submit.ios_locator is not None
        assert submit.android_locator is None

    def test_file_documentation(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Parser should extract file-level documentation."""
        filepath = sample_project_path / "resources" / "be" / "api" / "graphql.resource"
        rf = parse_file(filepath, cfg)
        assert "GraphQL" in rf.documentation

    def test_called_keywords_in_test_case(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """Parser should extract called keywords from test case bodies."""
        filepath = sample_project_path / "tests" / "login_test.robot"
        rf = parse_file(filepath, cfg)
        tc = next(tc for tc in rf.test_cases if tc.name == "Valid Login With Default Credentials")
        assert "Login With Valid Credentials" in tc.called_keywords

    def test_graphql_keywords(self, cfg: RAGConfig, sample_project_path: Path) -> None:
        """GraphQL resource should have mutation keywords."""
        filepath = sample_project_path / "resources" / "be" / "api" / "graphql.resource"
        rf = parse_file(filepath, cfg)
        kw_names = [kw.name for kw in rf.keywords]
        assert "Execute Create User Mutation" in kw_names
        assert "Execute Delete Account Mutation" in kw_names
        assert "Query User Profile" in kw_names
