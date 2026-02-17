"""Git-aware file crawler with .gitignore + hardcoded blacklist filtering."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterator

import pathspec

from rf_rag.config import HARDCODED_BLACKLIST, INGESTIBLE_EXTENSIONS, RF_ARTIFACT_NAMES

logger = logging.getLogger(__name__)


def _load_gitignore(project_root: Path) -> pathspec.PathSpec | None:
    """Load .gitignore patterns from the project root, if present."""
    gitignore = project_root / ".gitignore"
    if not gitignore.is_file():
        return None
    lines = gitignore.read_text(encoding="utf-8", errors="replace").splitlines()
    return pathspec.PathSpec.from_lines("gitwildmatch", lines)


def _is_blacklisted(path: Path, project_root: Path) -> bool:
    """Check if any path component matches the hardcoded blacklist."""
    try:
        rel = path.relative_to(project_root)
    except ValueError:
        return True
    for part in rel.parts:
        if part in HARDCODED_BLACKLIST:
            return True
    return False


def _is_rf_artifact(path: Path) -> bool:
    return path.name in RF_ARTIFACT_NAMES


def crawl(project_root: Path) -> Iterator[Path]:
    """Yield all ingestible .robot / .resource files under *project_root*.

    Filtering order:
      1. Hardcoded blacklist (directory name check)
      2. RF artifact names
      3. .gitignore patterns (via ``pathspec``)
      4. Extension whitelist
    """
    project_root = project_root.resolve()
    gitignore_spec = _load_gitignore(project_root)

    for path in sorted(project_root.rglob("*")):
        if not path.is_file():
            continue

        # 1 — blacklist
        if _is_blacklisted(path, project_root):
            continue

        # 2 — RF artifacts
        if _is_rf_artifact(path):
            continue

        # 3 — .gitignore
        if gitignore_spec is not None:
            rel_str = str(path.relative_to(project_root))
            if gitignore_spec.match_file(rel_str):
                continue

        # 4 — extension whitelist
        if path.suffix.lower() not in INGESTIBLE_EXTENSIONS:
            continue

        logger.debug("Crawled: %s", path.relative_to(project_root))
        yield path
