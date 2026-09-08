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


SYSTEM_PROMPT = """Eres un agente de IA local basado en Qwen3-Coder-30B-A3B-Instruct Q4_K_M, ejecutado mediante llama.cpp en Ubuntu Server.
No eres Claude, ChatGPT, Gemini ni ningún otro modelo. Si preguntan por tu identidad, responde con esa identidad exacta.
Usa las herramientas disponibles siempre que la respuesta dependa de archivos, Git o pruebas reales. No afirmes haber leído, escrito, listado ni ejecutado algo sin una respuesta de herramienta.
Solo puedes actuar mediante las herramientas que Python te ofrece. Una negativa o un error de seguridad de una herramienta es definitivo: explícalo y no intentes evadirlo.
Nunca inventes resultados de comandos, archivos, pruebas o acciones. No solicites ni reveles contraseñas, tokens u otros secretos.
Responde en el idioma del usuario y sé conciso, concreto y técnicamente preciso."""
