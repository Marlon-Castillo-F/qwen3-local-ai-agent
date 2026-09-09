from pathlib import Path

import pytest

from app.config import Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        workspace=tmp_path / "workspace",
        reports_dir=tmp_path / "reports",
        logs_dir=tmp_path / "logs",
        data_dir=tmp_path / "data",
        memory_db=tmp_path / "data" / "memory.db",
        knowledge_dir=tmp_path / "knowledge" / "sql-server",
        knowledge_db=tmp_path / "data" / "knowledge.db",
        request_timeout=5,
        tool_timeout=2,
    )
