"""Robot Framework file parser using ``robot.api``."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

from robot.api import get_model

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

logger = logging.getLogger(__name__)

# Regex for dict variable lines: &{NAME}  key=value  key2=value2
_DICT_VAR_RE = re.compile(r"^&\{(\w+)\}\s+(.+)$")
_KV_RE = re.compile(r"(\w+)=(.+)")


# ---------------------------------------------------------------------------
# Role & platform assignment helpers
# ---------------------------------------------------------------------------

def _assign_role(rel_path: str, cfg: RAGConfig) -> FileRole:
    """Determine the role of a file based on its relative path."""
    parts = rel_path.replace("\\", "/").lower()

    if parts.startswith(cfg.migration_dir.lower()):
        return FileRole.MIGRATION_TEST
    if parts.startswith(cfg.sit_dir.lower() + "/") or parts.startswith(cfg.sit_dir.lower() + "\\"):
        return FileRole.E2E_TEST
    if parts.startswith(cfg.tests_dir.lower()):
        return FileRole.ATOMIC_TEST

    # Resources sub-roles
    if "/po/" in parts or "\\po\\" in parts:
        return FileRole.PAGE_OBJECT
    if "/flow/" in parts or "\\flow\\" in parts:
        return FileRole.FLOW
    if "/api/" in parts or "\\api\\" in parts:
        return FileRole.API
    if parts.startswith(cfg.resources_dir.lower()):
        return FileRole.KNOWLEDGE_BASE

    if parts.startswith(cfg.data_dir_name.lower()):
        return FileRole.DATA_LAYER

    return FileRole.UNKNOWN


def _assign_platform(rel_path: str) -> Platform:
    parts = rel_path.replace("\\", "/").lower()
    if "/mobile/" in parts or "/ios/" in parts or "/android/" in parts:
        return Platform.IOS  # refined later per dict
    if "/web/" in parts:
        return Platform.WEB
    if "/be/" in parts:
        return Platform.BE
    if "/platform/" in parts:
        return Platform.COMMON
    return Platform.COMMON


# ---------------------------------------------------------------------------
# Body-text extraction helpers
# ---------------------------------------------------------------------------

def _body_to_text(body) -> str:
    """Convert a keyword/test body AST to a flat text representation."""
    lines: list[str] = []
    for item in body:
        data_tokens = [t.value for t in getattr(item, "data_tokens", []) if t.value]
        if data_tokens:
            lines.append("    ".join(data_tokens))
    return "\n".join(lines)


def _extract_called_keywords(body) -> list[str]:
    """Extract keyword names called from a body block."""
    calls: list[str] = []
    for item in body:
        # KeywordCall nodes have a .keyword attribute
        kw = getattr(item, "keyword", None)
        if kw:
            calls.append(kw)
    return calls


def _extract_setting(item, setting_name: str) -> Optional[str]:
    """Extract the value of a setting (e.g., [Setup], [Teardown]) from a test/keyword."""
    for child in getattr(item, "body", []):
        name = getattr(child, "type", "")
        if hasattr(child, "name") and child.name and child.name.lower() == setting_name.lower():
            tokens = [t.value for t in getattr(child, "data_tokens", []) if t.value]
            return " ".join(tokens) if tokens else None
        # Alternative: check by type string
        if name.upper() == setting_name.upper():
            tokens = [t.value for t in getattr(child, "data_tokens", []) if t.value]
            return " ".join(tokens) if tokens else None
    return None


# ---------------------------------------------------------------------------
# Main parse function
# ---------------------------------------------------------------------------

def parse_file(filepath: Path, cfg: RAGConfig) -> ResourceFile:
    """Parse a single .robot or .resource file into a ``ResourceFile`` model."""
    project_root = cfg.project_root.resolve()
    filepath = filepath.resolve()
    rel_path = str(filepath.relative_to(project_root))

    role = _assign_role(rel_path, cfg)
    platform = _assign_platform(rel_path)

    model = get_model(str(filepath))

    resource_name = filepath.stem

    # --- Collect documentation at file level ---
    file_doc = ""

    # --- Settings section: imports ---
    resource_imports: list[str] = []
    library_imports: list[str] = []

    for section in model.sections:
        section_type = type(section).__name__

        if "Setting" in section_type:
            for item in section.body:
                item_type = type(item).__name__
                if item_type == "ResourceImport":
                    resource_imports.append(getattr(item, "name", "") or "")
                elif item_type == "LibraryImport":
                    library_imports.append(getattr(item, "name", "") or "")
                elif item_type == "Documentation":
                    tokens = [t.value for t in getattr(item, "data_tokens", []) if t.value]
                    file_doc = " ".join(tokens)

    # --- Variables section ---
    variables: list[VariableDef] = []
    locator_mappings: list[LocatorMapping] = []
    ios_dict: dict[str, str] = {}
    android_dict: dict[str, str] = {}

    for section in model.sections:
        if "Variable" not in type(section).__name__:
            continue
        for item in section.body:
            item_type = type(item).__name__
            if item_type != "Variable":
                continue
            var_name = getattr(item, "name", "") or ""
            tokens = [t.value for t in getattr(item, "data_tokens", []) if t.value]
            value_repr = "    ".join(tokens)

            # Determine type from prefix
            if var_name.startswith("&"):
                vtype = "dict"
            elif var_name.startswith("@"):
                vtype = "list"
            else:
                vtype = "scalar"

            # Never store actual values for scalar secrets
            safe_value = value_repr
            lower_name = var_name.lower()
            if any(s in lower_name for s in ("password", "secret", "token", "key", "credential")):
                safe_value = "***REDACTED***"

            variables.append(VariableDef(
                name=var_name,
                value_repr=safe_value,
                source_file=rel_path,
                var_type=vtype,
            ))

            # Track IOS/ANDROID dicts for POM mapping
            clean_name = var_name.strip("&{}")
            if clean_name.upper() == "IOS":
                for kv_str in tokens:
                    m = _KV_RE.match(kv_str.strip())
                    if m:
                        ios_dict[m.group(1)] = m.group(2)
            elif clean_name.upper() == "ANDROID":
                for kv_str in tokens:
                    m = _KV_RE.match(kv_str.strip())
                    if m:
                        android_dict[m.group(1)] = m.group(2)

    # Build locator mappings from IOS + ANDROID dicts
    all_keys = set(ios_dict.keys()) | set(android_dict.keys())
    for key in sorted(all_keys):
        locator_mappings.append(LocatorMapping(
            element_name=key,
            ios_locator=ios_dict.get(key),
            android_locator=android_dict.get(key),
        ))

    # --- Keywords section ---
    keywords: list[KeywordDef] = []
    for section in model.sections:
        if "Keyword" not in type(section).__name__:
            continue
        for item in section.body:
            if type(item).__name__ != "Keyword":
                continue
            kw_name = getattr(item, "name", "") or ""
            kw_doc = ""
            kw_args: list[str] = []
            kw_tags: list[str] = []

            for child in getattr(item, "body", []):
                child_type = type(child).__name__
                if child_type == "Documentation":
                    tokens = [t.value for t in getattr(child, "data_tokens", []) if t.value]
                    kw_doc = " ".join(tokens)
                elif child_type == "Arguments":
                    tokens = [t.value for t in getattr(child, "data_tokens", []) if t.value]
                    kw_args = tokens
                elif child_type == "Tags":
                    tokens = [t.value for t in getattr(child, "data_tokens", []) if t.value]
                    kw_tags = tokens

            fqn = f"{resource_name}.{kw_name}"
            keywords.append(KeywordDef(
                name=kw_name,
                fqn=fqn,
                source_file=rel_path,
                documentation=kw_doc,
                arguments=kw_args,
                tags=kw_tags,
                body_text=_body_to_text(getattr(item, "body", [])),
                called_keywords=_extract_called_keywords(getattr(item, "body", [])),
                line_number=getattr(item, "lineno", 0),
            ))

    # --- Test Cases section ---
    test_cases: list[TestCaseDef] = []
    for section in model.sections:
        if "TestCase" not in type(section).__name__:
            continue
        for item in section.body:
            if type(item).__name__ != "TestCase":
                continue
            tc_name = getattr(item, "name", "") or ""
            tc_doc = ""
            tc_tags: list[str] = []
            tc_setup = None
            tc_teardown = None
            tc_template = None

            for child in getattr(item, "body", []):
                child_type = type(child).__name__
                if child_type == "Documentation":
                    tokens = [t.value for t in getattr(child, "data_tokens", []) if t.value]
                    tc_doc = " ".join(tokens)
                elif child_type == "Tags":
                    tokens = [t.value for t in getattr(child, "data_tokens", []) if t.value]
                    tc_tags = tokens
                elif child_type == "Setup":
                    tokens = [t.value for t in getattr(child, "data_tokens", []) if t.value]
                    tc_setup = tokens[0] if tokens else None
                elif child_type == "Teardown":
                    tokens = [t.value for t in getattr(child, "data_tokens", []) if t.value]
                    tc_teardown = tokens[0] if tokens else None
                elif child_type == "Template":
                    tokens = [t.value for t in getattr(child, "data_tokens", []) if t.value]
                    tc_template = tokens[0] if tokens else None

            fqn = f"{resource_name}.{tc_name}"
            test_cases.append(TestCaseDef(
                name=tc_name,
                fqn=fqn,
                source_file=rel_path,
                documentation=tc_doc,
                tags=tc_tags,
                setup=tc_setup,
                teardown=tc_teardown,
                template=tc_template,
                body_text=_body_to_text(getattr(item, "body", [])),
                called_keywords=_extract_called_keywords(getattr(item, "body", [])),
                line_number=getattr(item, "lineno", 0),
            ))

    return ResourceFile(
        rel_path=rel_path,
        role=role,
        platform=platform,
        documentation=file_doc,
        imports=resource_imports,
        library_imports=library_imports,
        keywords=keywords,
        test_cases=test_cases,
        variables=variables,
        locator_mappings=locator_mappings,
    )
