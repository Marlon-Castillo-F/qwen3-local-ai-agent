from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    api_base: str = os.getenv("AI_AGENT_API_BASE", "http://127.0.0.1:8080")
    model_reference: str = os.getenv(
        "AI_AGENT_MODEL",
        "lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M",
    )
    model_display_name: str = "Qwen3-Coder-30B-A3B-Instruct Q4_K_M"
    engine: str = "llama.cpp"
    threads: int = 24
    context_size: int = 8192
    workspace: Path = PROJECT_ROOT / "workspace"
    reports_dir: Path = PROJECT_ROOT / "reports"
    logs_dir: Path = PROJECT_ROOT / "logs"
    data_dir: Path = PROJECT_ROOT / "data"
    memory_db: Path = PROJECT_ROOT / "data" / "memory.db"
    knowledge_dir: Path = PROJECT_ROOT / "knowledge" / "sql-server"
    knowledge_db: Path = PROJECT_ROOT / "data" / "knowledge.db"
    request_timeout: int = 300
    tool_timeout: int = 120
    max_tool_rounds: int = 8
    max_file_bytes: int = 1024 * 1024
    max_tool_result_chars: int = 64 * 1024

    def ensure_directories(self) -> None:
        for directory in (
            self.workspace,
            self.reports_dir,
            self.logs_dir,
            self.data_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


SYSTEM_PROMPT_PATH = PROJECT_ROOT / "app" / "prompts" / "dba_system.md"


def load_system_prompt(path: Path = SYSTEM_PROMPT_PATH) -> str:
    prompt = path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"El system prompt está vacío: {path}")
    return prompt


SYSTEM_PROMPT = load_system_prompt()
