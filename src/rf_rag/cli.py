"""CLI entry point for rf-rag."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from rf_rag.config import RAGConfig
from rf_rag.engine import RAGEngine

console = Console()


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _make_engine(project_root: str, data_dir: str | None) -> RAGEngine:
    cfg = RAGConfig(
        project_root=Path(project_root),
        data_dir=Path(data_dir) if data_dir else None,
    )
    return RAGEngine(cfg)


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
def main(verbose: bool) -> None:
    """rf-rag — Autonomous AI-RAG for Robot Framework."""
    _setup_logging(verbose)


# ---------------------------------------------------------------------------
# ingest
# ---------------------------------------------------------------------------

@main.command()
@click.argument("project_root", type=click.Path(exists=True, file_okay=False))
@click.option("--data-dir", type=click.Path(), default=None,
              help="Custom directory for RAG data stores.")
def ingest(project_root: str, data_dir: str | None) -> None:
    """Crawl, parse, and index a Robot Framework project."""
    engine = _make_engine(project_root, data_dir)
    with console.status("[bold green]Ingesting project..."):
        stats = engine.ingest()

    table = Table(title="Ingestion Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green", justify="right")
    for k, v in stats.items():
        table.add_row(k, str(v))
    console.print(table)


# ---------------------------------------------------------------------------
# redundancy
# ---------------------------------------------------------------------------

@main.command()
@click.argument("project_root", type=click.Path(exists=True, file_okay=False))
@click.option("--threshold", type=float, default=0.90,
              help="Cosine similarity threshold (0.0–1.0).")
@click.option("--data-dir", type=click.Path(), default=None)
def redundancy(project_root: str, threshold: float, data_dir: str | None) -> None:
    """Detect multi-layer redundancy (horizontal, vertical, migration)."""
    engine = _make_engine(project_root, data_dir)
    engine.cfg.similarity_threshold = threshold

    with console.status("[bold green]Ingesting..."):
        engine.ingest()

    report = engine.redundancy()

    if not report.hits:
        console.print("[green]No redundancy detected.")
        return

    table = Table(title=f"Redundancy Report ({len(report.hits)} hits)")
    table.add_column("Kind", style="yellow")
    table.add_column("Source", style="cyan")
    table.add_column("Duplicate", style="red")
    table.add_column("Similarity", justify="right")
    table.add_column("Recommendation")

    for h in report.hits:
        table.add_row(h.kind, h.source_fqn, h.duplicate_fqn,
                       f"{h.similarity:.2%}", h.recommendation[:60])
    console.print(table)


# ---------------------------------------------------------------------------
# smoke
# ---------------------------------------------------------------------------

@main.command()
@click.argument("project_root", type=click.Path(exists=True, file_okay=False))
@click.option("-n", "--count", type=int, default=20, help="Number of smoke tests to select.")
@click.option("--data-dir", type=click.Path(), default=None)
def smoke(project_root: str, count: int, data_dir: str | None) -> None:
    """Select diverse smoke tests via Farthest Point Sampling."""
    engine = _make_engine(project_root, data_dir)

    with console.status("[bold green]Ingesting..."):
        engine.ingest()

    candidates = engine.smoke(n=count)

    table = Table(title=f"Smoke Test Selection ({len(candidates)} tests)")
    table.add_column("#", style="dim", justify="right")
    table.add_column("FQN", style="cyan")
    table.add_column("Source", style="blue")
    table.add_column("Tags", style="yellow")
    table.add_column("Diversity Score", justify="right")

    for i, c in enumerate(candidates, 1):
        table.add_row(str(i), c.fqn, c.source, ", ".join(c.tags), f"{c.distance_score:.4f}")
    console.print(table)


# ---------------------------------------------------------------------------
# query
# ---------------------------------------------------------------------------

@main.command()
@click.argument("project_root", type=click.Path(exists=True, file_okay=False))
@click.argument("text")
@click.option("-n", type=int, default=10, help="Max results.")
@click.option("--data-dir", type=click.Path(), default=None)
def query(project_root: str, text: str, n: int, data_dir: str | None) -> None:
    """Semantic search across the RF knowledge base."""
    engine = _make_engine(project_root, data_dir)

    with console.status("[bold green]Ingesting..."):
        engine.ingest()

    result = engine.query(text, n=n)
    console.print(f"[bold]{result.answer}")

    table = Table()
    table.add_column("FQN", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Source", style="blue")
    table.add_column("Distance", justify="right")
    table.add_column("Snippet")

    for item in result.items:
        table.add_row(
            item["fqn"], item["type"], item["source"],
            f"{item['distance']:.4f}", item["snippet"][:50],
        )
    console.print(table)


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

@main.command()
@click.argument("project_root", type=click.Path(exists=True, file_okay=False))
@click.option("--description", "-d", required=True, help="What the test should do.")
@click.option("--target", "-t", required=True, help="Target .robot file path (relative).")
@click.option("--tags", help="Comma-separated tags.")
@click.option("--platform", default="web", help="Target platform.")
@click.option("--data-dir", type=click.Path(), default=None)
def generate(project_root: str, description: str, target: str,
             tags: str | None, platform: str, data_dir: str | None) -> None:
    """Generate a DRY test suite using existing keywords."""
    engine = _make_engine(project_root, data_dir)

    with console.status("[bold green]Ingesting..."):
        engine.ingest()

    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    result = engine.generate(description, target, tags=tag_list, platform=platform)

    console.print(f"\n[bold green]Generated:[/] {result.filename}\n")
    console.print(result.content)

    if result.reused_keywords:
        console.print(f"\n[bold]Reused keywords:[/] {', '.join(result.reused_keywords)}")
    if result.import_chain:
        console.print(f"[bold]Import chain:[/] {', '.join(result.import_chain)}")
    if result.warnings:
        for w in result.warnings:
            console.print(f"[yellow]Warning:[/] {w}")


# ---------------------------------------------------------------------------
# inventory
# ---------------------------------------------------------------------------

@main.command()
@click.argument("project_root", type=click.Path(exists=True, file_okay=False))
@click.option("--type", "inv_type", type=click.Choice(["keywords", "tests", "graphql", "po"]),
              default="keywords", help="Inventory type.")
@click.option("--data-dir", type=click.Path(), default=None)
def inventory(project_root: str, inv_type: str, data_dir: str | None) -> None:
    """Run inventory queries against the knowledge base."""
    engine = _make_engine(project_root, data_dir)

    with console.status("[bold green]Ingesting..."):
        engine.ingest()

    if inv_type == "keywords":
        result = engine.inventory_keywords()
    elif inv_type == "tests":
        result = engine.inventory_tests()
    elif inv_type == "graphql":
        result = engine.graphql_coverage()
    elif inv_type == "po":
        result = engine.po_mismatches()
    else:
        console.print("[red]Unknown inventory type.")
        return

    console.print(f"[bold]{result.answer}\n")
    console.print(json.dumps(result.items, indent=2))


if __name__ == "__main__":
    main()
