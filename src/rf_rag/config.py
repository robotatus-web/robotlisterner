"""Central configuration for the RF-RAG system."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


# Directories / files that are always excluded regardless of .gitignore
HARDCODED_BLACKLIST: set[str] = {
    "venv",
    ".venv",
    "__pycache__",
    ".git",
    "pabot",
    "node_modules",
    ".rf_rag_data",
}

# RF output artifacts to skip
RF_ARTIFACT_NAMES: set[str] = {
    "output.xml",
    "report.html",
    "log.html",
}

# File extensions the system will ingest
INGESTIBLE_EXTENSIONS: set[str] = {".robot", ".resource"}


class RAGConfig(BaseModel):
    """Runtime configuration for one project."""

    project_root: Path
    data_dir: Optional[Path] = None  # defaults to project_root / .rf_rag_data
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384  # must match embedding_model output dimension
    smoke_test_count: int = 20
    similarity_threshold: float = 0.90  # for redundancy detection

    # Neo4j settings
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4j"
    neo4j_database: str = "neo4j"

    # Qdrant settings (None = in-memory mode)
    qdrant_url: Optional[str] = None
    qdrant_path: Optional[str] = None
    qdrant_collection: str = "rf_rag"

    def effective_data_dir(self) -> Path:
        d = self.data_dir or (self.project_root / ".rf_rag_data")
        d.mkdir(parents=True, exist_ok=True)
        return d

    # Convenience: role-assignment path prefixes (relative to project_root)
    tests_dir: str = "tests"
    sit_dir: str = "SIT"
    resources_dir: str = "resources"
    data_dir_name: str = "data"
    migration_dir: str = Field(default="tests/migration")
