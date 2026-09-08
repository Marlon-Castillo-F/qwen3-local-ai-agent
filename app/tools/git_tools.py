from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _run_git(cwd: Path, arguments: list[str], *, timeout: int) -> str:
    environment = os.environ.copy()
    environment.update({"GIT_PAGER": "cat", "PAGER": "cat"})
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(f"Git excedió el timeout de {timeout} segundos") from exc
    output = (completed.stdout + completed.stderr).strip()
    if completed.returncode != 0:
        raise ValueError(output or f"Git terminó con código {completed.returncode}")
    return output


def git_status(workspace: Path, *, timeout: int = 30) -> str:
    return _run_git(
        workspace,
        ["status", "--short", "--branch", "--untracked-files=normal"],
        timeout=timeout,
    ) or "Árbol de trabajo limpio"


def git_diff(workspace: Path, *, timeout: int = 30) -> str:
    unstaged = _run_git(workspace, ["diff", "--no-ext-diff", "--"], timeout=timeout)
    staged = _run_git(
        workspace, ["diff", "--cached", "--no-ext-diff", "--"], timeout=timeout
    )
    sections = []
    if unstaged:
        sections.append("[UNSTAGED]\n" + unstaged)
    if staged:
        sections.append("[STAGED]\n" + staged)
    return "\n\n".join(sections) or "No hay diferencias"
