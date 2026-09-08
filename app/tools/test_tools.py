from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ALLOWED_COMMANDS = {
    "python -m pytest": lambda root: [sys.executable, "-m", "pytest", "-q"],
    "pytest": lambda root: [str(root / ".venv" / "bin" / "pytest"), "-q"],
}


def run_tests(
    command: str = "python -m pytest",
    *,
    project_root: Path,
    timeout: int = 120,
) -> str:
    factory = ALLOWED_COMMANDS.get(command)
    if factory is None:
        raise PermissionError(f"Comando de pruebas no permitido: {command}")
    arguments = factory(project_root)
    try:
        completed = subprocess.run(
            arguments,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(f"Las pruebas excedieron {timeout} segundos") from exc
    output = (completed.stdout + completed.stderr).strip()
    return f"exit_code={completed.returncode}\n{output}"
