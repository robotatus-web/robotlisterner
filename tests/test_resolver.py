"""Tests for the recursive resource resolver."""

from __future__ import annotations

from pathlib import Path

import pytest

from rf_rag.config import RAGConfig
from rf_rag.crawler import crawl
from rf_rag.models import FileRole, ResourceFile
from rf_rag.parser import parse_file
from rf_rag.resolver import ResourceResolver


@pytest.fixture
def file_map(sample_project_path: Path) -> dict[str, ResourceFile]:
    """Parse all files in the sample project into a file_map."""
    cfg = RAGConfig(project_root=sample_project_path)
    fmap: dict[str, ResourceFile] = {}
    for filepath in crawl(sample_project_path):
        rf = parse_file(filepath, cfg)
        fmap[rf.rel_path] = rf
    return fmap


@pytest.fixture
def resolver(file_map: dict[str, ResourceFile], sample_project_path: Path) -> ResourceResolver:
    return ResourceResolver(file_map, sample_project_path)


class TestResourceResolver:
    """Test ResourceResolver with the sample project."""

    def test_effective_keywords_includes_own(
        self, resolver: ResourceResolver, file_map: dict[str, ResourceFile]
    ) -> None:
        """A file's effective scope should include its own keywords."""
        flow_path = next(k for k in file_map if "login_flow" in k)
        keywords = resolver.effective_keywords(flow_path)
        fqns = [kw.fqn for kw in keywords]
        assert any("Login With Valid Credentials" in fqn for fqn in fqns)

    def test_effective_keywords_includes_imported(
        self, resolver: ResourceResolver, file_map: dict[str, ResourceFile]
    ) -> None:
        """A file's effective scope should include keywords from imported files."""
        flow_path = next(k for k in file_map if "login_flow" in k)
        keywords = resolver.effective_keywords(flow_path)
        fqns = [kw.fqn for kw in keywords]
        # login_flow imports login_page, so PO keywords should be in scope
        assert any("Input Login Credentials" in fqn for fqn in fqns)

    def test_common_resource_transitive_scope(
        self, resolver: ResourceResolver, file_map: dict[str, ResourceFile]
    ) -> None:
        """common.resource should transitively include all sub-resource keywords."""
        common_path = next(k for k in file_map if "common" in k)
        keywords = resolver.effective_keywords(common_path)
        fqns = [kw.fqn for kw in keywords]
        # common imports login_flow, login_page, graphql, GlobalVariables
        assert any("Login With Valid Credentials" in fqn for fqn in fqns)
        assert any("Input Login Credentials" in fqn for fqn in fqns)
        assert any("Execute Create User Mutation" in fqn for fqn in fqns)

    def test_test_file_scope_via_common(
        self, resolver: ResourceResolver, file_map: dict[str, ResourceFile]
    ) -> None:
        """A test file importing common.resource should see all keywords."""
        test_path = next(k for k in file_map if "login_test" in k and "migration" not in k)
        keywords = resolver.effective_keywords(test_path)
        fqns = [kw.fqn for kw in keywords]
        # test file imports common -> includes everything
        assert any("Login With Valid Credentials" in fqn for fqn in fqns)
        assert any("Execute Create User Mutation" in fqn for fqn in fqns)

    def test_imported_files_returns_all_transitively(
        self, resolver: ResourceResolver, file_map: dict[str, ResourceFile]
    ) -> None:
        """imported_files() should return all transitively imported files."""
        common_path = next(k for k in file_map if "common" in k)
        imported = resolver.imported_files(common_path)
        # common imports several files directly and transitively
        assert len(imported) >= 3  # at least common itself + a few imports

    def test_circular_import_handling(self, tmp_path: Path) -> None:
        """Resolver should handle circular imports without infinite loop."""
        # Create two files that import each other
        (tmp_path / "a.resource").write_text(
            "*** Settings ***\nResource    b.resource\n"
            "*** Keywords ***\nKW A\n    Log    A\n"
        )
        (tmp_path / "b.resource").write_text(
            "*** Settings ***\nResource    a.resource\n"
            "*** Keywords ***\nKW B\n    Log    B\n"
        )
        cfg = RAGConfig(project_root=tmp_path)
        fmap = {}
        for f in [tmp_path / "a.resource", tmp_path / "b.resource"]:
            rf = parse_file(f, cfg)
            fmap[rf.rel_path] = rf
        resolver = ResourceResolver(fmap, tmp_path)
        # Should not hang — should return keywords from both files
        kws = resolver.effective_keywords("a.resource")
        fqns = [kw.fqn for kw in kws]
        assert any("KW A" in fqn for fqn in fqns)
        assert any("KW B" in fqn for fqn in fqns)

    def test_scope_caching(
        self, resolver: ResourceResolver, file_map: dict[str, ResourceFile]
    ) -> None:
        """Second call to effective_keywords should return cached result."""
        common_path = next(k for k in file_map if "common" in k)
        result1 = resolver.effective_keywords(common_path)
        result2 = resolver.effective_keywords(common_path)
        assert result1 is result2  # same object (cached)
