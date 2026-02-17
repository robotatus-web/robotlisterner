"""Shared fixtures for rf-rag unit tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rf_rag.config import RAGConfig
from rf_rag.models import (
    FileRole,
    KeywordDef,
    LocatorMapping,
    Platform,
    ResourceFile,
    TestCaseDef,
    VariableDef,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sample_project"


@pytest.fixture
def sample_project_path() -> Path:
    """Path to the sample RF project used in tests."""
    return FIXTURES_DIR


@pytest.fixture
def rag_config(sample_project_path: Path) -> RAGConfig:
    """RAGConfig pointing at the sample project with in-memory Qdrant."""
    return RAGConfig(
        project_root=sample_project_path,
        # in-memory Qdrant (qdrant_url=None, qdrant_path=None)
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="neo4j",
    )


@pytest.fixture
def sample_resource_file() -> ResourceFile:
    """A minimal ResourceFile for unit-level tests."""
    return ResourceFile(
        rel_path="resources/web/flow/login_flow.resource",
        role=FileRole.FLOW,
        platform=Platform.WEB,
        documentation="Business-level login flow keywords.",
        imports=["resources/web/po/login_page.resource"],
        keywords=[
            KeywordDef(
                name="Login With Valid Credentials",
                fqn="login_flow.Login With Valid Credentials",
                source_file="resources/web/flow/login_flow.resource",
                documentation="Performs a complete login using valid default credentials.",
                tags=["web", "smoke"],
                body_text="Verify Login Page Loaded\nInput Login Credentials\nClick Login Button",
                called_keywords=["Verify Login Page Loaded", "Input Login Credentials",
                                 "Click Login Button"],
                line_number=7,
            ),
        ],
        test_cases=[],
        variables=[],
        locator_mappings=[],
    )


@pytest.fixture
def sample_test_file() -> ResourceFile:
    """A minimal test ResourceFile for unit-level tests."""
    return ResourceFile(
        rel_path="tests/login_test.robot",
        role=FileRole.ATOMIC_TEST,
        platform=Platform.WEB,
        documentation="Atomic login validation tests.",
        imports=["resources/platform/common.resource"],
        keywords=[
            KeywordDef(
                name="Base Data Creation",
                fqn="login_test.Base Data Creation",
                source_file="tests/login_test.robot",
                documentation="Setup test data for login tests.",
                tags=[],
                body_text="Log    Creating base data\nExecute Create User Mutation",
                called_keywords=["Execute Create User Mutation"],
                line_number=20,
            ),
        ],
        test_cases=[
            TestCaseDef(
                name="Valid Login With Default Credentials",
                fqn="login_test.Valid Login With Default Credentials",
                source_file="tests/login_test.robot",
                documentation="Verify that a user can log in with valid default credentials.",
                tags=["web", "smoke", "login"],
                setup="Base Data Creation",
                teardown="Cleanup And Logout",
                body_text="Login With Valid Credentials",
                called_keywords=["Login With Valid Credentials"],
                line_number=7,
            ),
        ],
        variables=[],
        locator_mappings=[],
    )


@pytest.fixture
def sample_po_file() -> ResourceFile:
    """A POM ResourceFile with locator mappings (one intentionally mismatched)."""
    return ResourceFile(
        rel_path="resources/web/po/login_page.resource",
        role=FileRole.PAGE_OBJECT,
        platform=Platform.WEB,
        documentation="Page Object for the Login page.",
        imports=[],
        keywords=[
            KeywordDef(
                name="Input Login Credentials",
                fqn="login_page.Input Login Credentials",
                source_file="resources/web/po/login_page.resource",
                documentation="Enters username and password on the login page.",
                arguments=["${username}", "${password}"],
                tags=[],
                body_text="Input Text    ${username_field}    ${username}",
                called_keywords=[],
                line_number=16,
            ),
        ],
        test_cases=[],
        variables=[
            VariableDef(name="&{IOS}", value_repr="login_btn=...", var_type="dict"),
            VariableDef(name="&{ANDROID}", value_repr="login_btn=...", var_type="dict"),
        ],
        locator_mappings=[
            LocatorMapping(
                element_name="login_btn",
                ios_locator="//XCUIElementTypeButton[@name='Login']",
                android_locator="//android.widget.Button[@text='Login']",
            ),
            LocatorMapping(
                element_name="username_field",
                ios_locator="//XCUIElementTypeTextField[@name='Username']",
                android_locator="//android.widget.EditText[@hint='Username']",
            ),
            LocatorMapping(
                element_name="password_field",
                ios_locator="//XCUIElementTypeSecureTextField[@name='Password']",
                android_locator="//android.widget.EditText[@hint='Password']",
            ),
            # Intentionally mismatched — submit_btn only in IOS
            LocatorMapping(
                element_name="submit_btn",
                ios_locator="//XCUIElementTypeButton[@name='Submit']",
                android_locator=None,
            ),
        ],
    )


@pytest.fixture
def mock_neo4j_driver():
    """Create a mocked Neo4j driver that doesn't require a running server."""
    with patch("rf_rag.graph.GraphDatabase") as mock_gdb:
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)
        mock_gdb.driver.return_value = mock_driver
        yield mock_driver, mock_session
