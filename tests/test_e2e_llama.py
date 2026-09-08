import os
from pathlib import Path

import pytest

from app.agent import Agent
from app.client import LlamaClient
from app.config import Settings
from app.memory import MemoryStore
from app.tools import build_registry
from app.tools.files import write_file


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_E2E") != "1",
    reason="requiere RUN_LIVE_E2E=1 y llama-server local",
)


def _live_agent(settings: Settings, database: Path) -> Agent:
    memory = MemoryStore(database)
    return Agent(LlamaClient(settings), build_registry(settings), memory, settings)


def test_live_model_lists_real_file(tmp_path: Path):
    settings = Settings()
    marker = "codex_e2e_listado.txt"
    target = settings.workspace / marker
    write_file(marker, "archivo para prueba end to end", workspace=settings.workspace)
    agent = _live_agent(settings, tmp_path / "list.db")
    events = []
    try:
        answer = agent.run(
            f"Lista el workspace usando list_files y dime si existe {marker}.",
            lambda kind, value: events.append((kind, value)),
        )
        assert ("tool_call", "list_files") in events
        assert any(marker in value for kind, value in events if kind == "tool_result")
        assert marker.casefold() in answer.casefold()
    finally:
        agent.memory.close()
        target.unlink(missing_ok=True)


def test_live_model_reads_real_file(tmp_path: Path):
    settings = Settings()
    marker_file = "codex_e2e_lectura.txt"
    marker_text = "MARCADOR-E2E-QWEN-7391"
    target = settings.workspace / marker_file
    write_file(marker_file, marker_text, workspace=settings.workspace)
    agent = _live_agent(settings, tmp_path / "read.db")
    events = []
    try:
        answer = agent.run(
            f"Usa read_file para leer {marker_file} y repite exactamente su contenido.",
            lambda kind, value: events.append((kind, value)),
        )
        assert ("tool_call", "read_file") in events
        assert any(marker_text in value for kind, value in events if kind == "tool_result")
        assert marker_text in answer
    finally:
        agent.memory.close()
        target.unlink(missing_ok=True)
