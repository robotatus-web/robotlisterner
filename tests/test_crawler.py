"""Tests for the file crawler module."""

from __future__ import annotations

from pathlib import Path

from rf_rag.crawler import crawl


class TestCrawl:
    """Test crawl() function with the sample project fixture."""

    def test_finds_robot_files(self, sample_project_path: Path) -> None:
        """Crawl should find .robot files."""
        files = list(crawl(sample_project_path))
        robot_files = [f for f in files if f.suffix == ".robot"]
        assert len(robot_files) >= 3  # login_test, migration_test, e2e

    def test_finds_resource_files(self, sample_project_path: Path) -> None:
        """Crawl should find .resource files."""
        files = list(crawl(sample_project_path))
        resource_files = [f for f in files if f.suffix == ".resource"]
        assert len(resource_files) >= 4  # common, login_page, login_flow, graphql, GlobalVars

    def test_excludes_gitignore_patterns(self, sample_project_path: Path, tmp_path: Path) -> None:
        """Crawl should respect .gitignore patterns."""
        # Create a project with .gitignore
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / ".gitignore").write_text("ignored_dir/\n")
        (proj / "good.robot").write_text("*** Test Cases ***\nTest\n    Log    ok\n")
        ignored = proj / "ignored_dir"
        ignored.mkdir()
        (ignored / "bad.robot").write_text("*** Test Cases ***\nTest\n    Log    bad\n")

        files = [f.name for f in crawl(proj)]
        assert "good.robot" in files
        assert "bad.robot" not in files

    def test_excludes_blacklisted_dirs(self, tmp_path: Path) -> None:
        """Crawl should exclude hardcoded blacklisted directories."""
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / "good.robot").write_text("*** Test Cases ***\nTest\n    Log    ok\n")
        pabot = proj / "pabot"
        pabot.mkdir()
        (pabot / "bad.robot").write_text("*** Test Cases ***\nTest\n    Log    bad\n")
        pycache = proj / "__pycache__"
        pycache.mkdir()
        (pycache / "cached.robot").write_text("*** Test Cases ***\nTest\n    Log    cached\n")

        files = [f.name for f in crawl(proj)]
        assert "good.robot" in files
        assert "bad.robot" not in files
        assert "cached.robot" not in files

    def test_excludes_rf_artifacts(self, tmp_path: Path) -> None:
        """Crawl should exclude RF artifact files (output.xml, log.html, report.html)."""
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / "good.robot").write_text("*** Test Cases ***\nTest\n    Log    ok\n")
        (proj / "output.xml").write_text("<xml/>")
        (proj / "report.html").write_text("<html/>")
        (proj / "log.html").write_text("<html/>")

        files = [f.name for f in crawl(proj)]
        assert "good.robot" in files
        assert "output.xml" not in files
        assert "report.html" not in files
        assert "log.html" not in files

    def test_excludes_non_rf_extensions(self, tmp_path: Path) -> None:
        """Crawl should only include .robot and .resource files."""
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / "good.robot").write_text("*** Test Cases ***\nTest\n    Log    ok\n")
        (proj / "readme.md").write_text("# Readme")
        (proj / "script.py").write_text("print('hello')")

        files = [f.name for f in crawl(proj)]
        assert "good.robot" in files
        assert "readme.md" not in files
        assert "script.py" not in files

    def test_total_fixture_file_count(self, sample_project_path: Path) -> None:
        """Verify the total number of RF files found in the sample project."""
        files = list(crawl(sample_project_path))
        # 3 .robot + 5 .resource = 8 files
        assert len(files) == 8
