"""Recursive resource resolver — computes the *Effective Scope* of any file."""

from __future__ import annotations

import logging
from pathlib import Path

from rf_rag.models import KeywordDef, ResourceFile

logger = logging.getLogger(__name__)


class ResourceResolver:
    """Resolves the full keyword scope of any file by following its import chain.

    Given a mapping of ``{rel_path: ResourceFile}``, this resolver walks the
    ``imports`` list of each file recursively and collects every keyword that
    is available at runtime (the "Effective Scope").
    """

    def __init__(self, file_map: dict[str, ResourceFile], project_root: Path) -> None:
        self._file_map = file_map
        self._project_root = project_root.resolve()
        # Cache: rel_path -> list of keywords in effective scope
        self._scope_cache: dict[str, list[KeywordDef]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def effective_keywords(self, rel_path: str) -> list[KeywordDef]:
        """Return every keyword available in the scope of *rel_path*."""
        if rel_path in self._scope_cache:
            return self._scope_cache[rel_path]

        visited: set[str] = set()
        result: list[KeywordDef] = []
        self._walk(rel_path, visited, result)
        self._scope_cache[rel_path] = result
        return result

    def imported_files(self, rel_path: str) -> list[str]:
        """Return every file transitively imported by *rel_path* (including itself)."""
        visited: set[str] = set()
        self._walk_files(rel_path, visited)
        return sorted(visited)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _resolve_import(self, importing_file: str, import_path: str) -> str | None:
        """Resolve an import path to a rel_path key in the file map.

        Robot Framework uses paths relative to the importing file's directory.
        Variables like ``${CURDIR}`` are replaced with ``.``.
        """
        import_path = import_path.replace("${CURDIR}", ".").replace("%{CURDIR}", ".")
        # Strip surrounding whitespace
        import_path = import_path.strip()

        importing_dir = (self._project_root / importing_file).parent
        candidate = (importing_dir / import_path).resolve()

        try:
            resolved_rel = str(candidate.relative_to(self._project_root))
        except ValueError:
            logger.debug("Import %s resolves outside project root", import_path)
            return None

        # Normalise separators
        resolved_rel = resolved_rel.replace("\\", "/")

        # Try exact match first
        if resolved_rel in self._file_map:
            return resolved_rel

        # Try with OS-native separators
        for key in self._file_map:
            if key.replace("\\", "/") == resolved_rel:
                return key

        logger.debug("Unresolved import: %s (from %s)", import_path, importing_file)
        return None

    def _walk(self, rel_path: str, visited: set[str], acc: list[KeywordDef]) -> None:
        if rel_path in visited:
            return
        visited.add(rel_path)

        rf = self._file_map.get(rel_path)
        if rf is None:
            return

        # Add own keywords
        acc.extend(rf.keywords)

        # Recurse into imports
        for imp in rf.imports:
            resolved = self._resolve_import(rel_path, imp)
            if resolved:
                self._walk(resolved, visited, acc)

    def _walk_files(self, rel_path: str, visited: set[str]) -> None:
        if rel_path in visited:
            return
        visited.add(rel_path)

        rf = self._file_map.get(rel_path)
        if rf is None:
            return

        for imp in rf.imports:
            resolved = self._resolve_import(rel_path, imp)
            if resolved:
                self._walk_files(resolved, visited)
