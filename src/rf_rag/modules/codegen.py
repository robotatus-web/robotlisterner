"""Module 4: Context-Aware Code Generation (DRY Agent).

Generates Robot Framework code (test suites, keywords) following project
conventions:
  - Priority: Global Flow > Platform Keyword > PO Keyword.
  - Imports resolved via the global resource chain with relative paths.
  - Base Data Creation generated locally using existing patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from rf_rag.graph import RFGraph
from rf_rag.models import FileRole, ResourceFile
from rf_rag.resolver import ResourceResolver
from rf_rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class GeneratedCode:
    """Result of code generation."""

    filename: str
    content: str
    import_chain: list[str]
    reused_keywords: list[str]
    warnings: list[str]


class DRYCodeGenerator:
    """Generates RF code that maximally reuses existing keywords (DRY principle).

    Workflow:
      1. Accept a natural-language description of the desired test/keyword.
      2. Search the vector store for similar existing keywords.
      3. Compose the result by referencing existing keywords instead of
         duplicating logic.
      4. Resolve imports using the resource chain.
    """

    def __init__(
        self,
        graph: RFGraph,
        vector_store: VectorStore,
        file_map: dict[str, ResourceFile],
        resolver: ResourceResolver,
    ) -> None:
        self._graph = graph
        self._vs = vector_store
        self._file_map = file_map
        self._resolver = resolver

    def generate_test_suite(
        self,
        description: str,
        target_path: str,
        tags: list[str] | None = None,
        platform: str = "web",
    ) -> GeneratedCode:
        """Generate a new test suite .robot file.

        Args:
            description: Natural-language description of the test.
            target_path: Relative path where the file will live (for import resolution).
            tags: Tags to apply to the test case.
            platform: Target platform (web, ios, android).
        """
        tags = tags or [platform]
        warnings: list[str] = []

        # 1. Search for relevant existing keywords
        results = self._vs.search(description, n_results=15)

        # Prioritise by role: Flow > Platform KW > PO
        priority_order = {
            FileRole.FLOW.value: 0,
            FileRole.KNOWLEDGE_BASE.value: 1,
            FileRole.PAGE_OBJECT.value: 2,
            FileRole.API.value: 3,
        }
        results.sort(key=lambda r: priority_order.get(r["metadata"].get("role", ""), 99))

        # Select top keywords to reuse
        reused: list[dict[str, Any]] = []
        seen_fqns: set[str] = set()
        for r in results:
            fqn = r["metadata"].get("fqn", "")
            if fqn and fqn not in seen_fqns and r["metadata"].get("type") == "keyword":
                reused.append(r["metadata"])
                seen_fqns.add(fqn)
            if len(reused) >= 5:
                break

        # 2. Find a suitable import chain
        #    Strategy: find the common resource file that gives access to the most reused keywords
        import_chain = self._find_best_import(target_path, reused)

        # 3. Find Base Data Creation pattern from similar suites
        base_data_pattern = self._find_base_data_pattern(description)

        # 4. Generate the .robot content
        content = self._render_suite(
            description=description,
            tags=tags,
            import_chain=import_chain,
            reused_keywords=reused,
            base_data_pattern=base_data_pattern,
        )

        return GeneratedCode(
            filename=target_path,
            content=content,
            import_chain=import_chain,
            reused_keywords=[r.get("fqn", "") for r in reused],
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_best_import(self, target_path: str, reused: list[dict]) -> list[str]:
        """Find the minimal set of Resource imports to access reused keywords."""
        needed_sources: set[str] = set()
        for r in reused:
            src = r.get("source", "")
            if src:
                needed_sources.add(src)

        # Check which single file, through recursive imports, covers the most sources
        best_file = ""
        best_coverage = 0
        for rel_path in self._file_map:
            imported = set(self._resolver.imported_files(rel_path))
            coverage = len(needed_sources & imported)
            if coverage > best_coverage:
                best_coverage = coverage
                best_file = rel_path

        if best_file:
            # Compute relative path from target to best_file
            rel_import = _relative_path(target_path, best_file)
            return [rel_import]

        # Fallback: import each source directly
        return [_relative_path(target_path, s) for s in sorted(needed_sources)]

    def _find_base_data_pattern(self, description: str) -> str:
        """Search for an existing Base Data Creation keyword to use as template."""
        results = self._vs.search("Base Data Creation setup", n_results=3,
                                   where={"type": "keyword"})
        if results:
            # Use the closest match's body as a pattern
            best = results[0]
            return best.get("document", "")
        return ""

    def _render_suite(
        self,
        description: str,
        tags: list[str],
        import_chain: list[str],
        reused_keywords: list[dict],
        base_data_pattern: str,
    ) -> str:
        """Render a .robot file from components."""
        lines: list[str] = []

        # Settings
        lines.append("*** Settings ***")
        for imp in import_chain:
            lines.append(f"Resource          {imp}")
        lines.append("")

        # Test Cases
        test_name = description.replace(".", "").strip()[:80]
        lines.append("*** Test Cases ***")
        lines.append(test_name)
        lines.append(f"    [Documentation]    {description}")
        lines.append(f"    [Tags]             {'    '.join(tags)}")
        lines.append("    [Setup]            Base Data Creation")

        # Add calls to reused keywords
        for kw in reused_keywords:
            kw_name = kw.get("name", kw.get("fqn", ""))
            lines.append(f"    {kw_name}")

        lines.append("    [Teardown]         Cleanup And Logout")
        lines.append("")

        # Keywords section — Base Data Creation
        lines.append("*** Keywords ***")
        lines.append("Base Data Creation")
        lines.append("    [Documentation]    Local setup logic (auto-generated).")
        if base_data_pattern:
            # Re-use the pattern from a similar suite
            for pat_line in base_data_pattern.strip().split("\n"):
                stripped = pat_line.strip()
                if stripped and not stripped.startswith("["):
                    lines.append(f"    {stripped}")
        else:
            lines.append("    Log    Setup placeholder — customize for this suite.")
        lines.append("")

        return "\n".join(lines) + "\n"


def _relative_path(from_file: str, to_file: str) -> str:
    """Compute a relative path from *from_file*'s directory to *to_file*."""
    from_dir = PurePosixPath(from_file).parent
    to_path = PurePosixPath(to_file)

    # Find common prefix
    from_parts = list(from_dir.parts) if str(from_dir) != "." else []
    to_parts = list(to_path.parts)

    common = 0
    for a, b in zip(from_parts, to_parts):
        if a == b:
            common += 1
        else:
            break

    ups = len(from_parts) - common
    remaining = to_parts[common:]

    parts = [".."] * ups + remaining
    return "/".join(parts) if parts else to_file
