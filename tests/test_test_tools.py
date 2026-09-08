import subprocess
from pathlib import Path

import pytest

from app.tools.test_tools import run_tests


def test_disallowed_test_command(tmp_path: Path):
    with pytest.raises(PermissionError):
        run_tests("sudo pytest", project_root=tmp_path)


def test_test_timeout(monkeypatch, tmp_path: Path):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], timeout=1)

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(TimeoutError):
        run_tests("python -m pytest", project_root=tmp_path, timeout=1)


def test_allowed_command_uses_no_shell(monkeypatch, tmp_path: Path):
    observed = {}

    def fake_run(args, **kwargs):
        observed["args"] = args
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(args, 0, "ok", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = run_tests("python -m pytest", project_root=tmp_path)
    assert observed["args"][1:3] == ["-m", "pytest"]
    assert "shell" not in observed["kwargs"]
    assert result == "exit_code=0\nok"
