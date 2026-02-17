"""Pydantic domain models for the RF-RAG system."""

from __future__ import annotations

from enum import Enum
from pathlib import PurePosixPath
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class FileRole(str, Enum):
    """Role assigned to a file based on its location in the project tree."""

    ATOMIC_TEST = "ATOMIC_TESTS"
    E2E_TEST = "E2E_TESTS"
    KNOWLEDGE_BASE = "KNOWLEDGE_BASE"
    DATA_LAYER = "DATA_LAYER"
    PAGE_OBJECT = "PAGE_OBJECT"
    FLOW = "FLOW"
    API = "API"
    MIGRATION_TEST = "MIGRATION_TESTS"
    UNKNOWN = "UNKNOWN"


class Platform(str, Enum):
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"
    BE = "be"
    COMMON = "common"


class KeywordScope(str, Enum):
    """Where a keyword is defined."""

    LOCAL = "local"
    RESOURCE = "resource"
    LIBRARY = "library"


# ---------------------------------------------------------------------------
# Core domain objects
# ---------------------------------------------------------------------------

class LocatorMapping(BaseModel):
    """A single UI element with per-platform locators."""

    element_name: str
    ios_locator: Optional[str] = None
    android_locator: Optional[str] = None


class KeywordDef(BaseModel):
    """A parsed Robot Framework keyword definition."""

    name: str
    fqn: str = ""  # ResourceName.KeywordName
    source_file: str = ""  # relative to PROJECT_ROOT
    documentation: str = ""
    arguments: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    body_text: str = ""  # raw body for embedding
    called_keywords: list[str] = Field(default_factory=list)
    line_number: int = 0


class TestCaseDef(BaseModel):
    """A parsed Robot Framework test case."""

    name: str
    fqn: str = ""
    source_file: str = ""
    documentation: str = ""
    tags: list[str] = Field(default_factory=list)
    setup: Optional[str] = None
    teardown: Optional[str] = None
    template: Optional[str] = None
    body_text: str = ""
    called_keywords: list[str] = Field(default_factory=list)
    line_number: int = 0


class VariableDef(BaseModel):
    """A parsed variable (scalar, list, or dict)."""

    name: str
    value_repr: str = ""  # representation only — never store secrets
    source_file: str = ""
    var_type: str = "scalar"  # scalar | list | dict


class ResourceFile(BaseModel):
    """Represents one parsed .resource or .robot file."""

    rel_path: str  # relative to PROJECT_ROOT
    role: FileRole = FileRole.UNKNOWN
    platform: Platform = Platform.COMMON
    documentation: str = ""
    imports: list[str] = Field(default_factory=list)  # relative resource paths
    library_imports: list[str] = Field(default_factory=list)
    keywords: list[KeywordDef] = Field(default_factory=list)
    test_cases: list[TestCaseDef] = Field(default_factory=list)
    variables: list[VariableDef] = Field(default_factory=list)
    locator_mappings: list[LocatorMapping] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Graph edge types
# ---------------------------------------------------------------------------

class EdgeType(str, Enum):
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    DEFINES = "DEFINES"
    TESTS = "TESTS"
    TAGGED = "TAGGED"
    MAPS_ELEMENT = "MAPS_ELEMENT"


class GraphEdge(BaseModel):
    source: str
    target: str
    edge_type: EdgeType
    metadata: dict = Field(default_factory=dict)
