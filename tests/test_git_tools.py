import subprocess
from pathlib import Path

from app.tools.git_tools import git_diff, git_status


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def test_git_status_and_diff(tmp_path: Path):
    root = tmp_path / "repo"
    workspace = root / "workspace"
    workspace.mkdir(parents=True)
    _git(root, "init")
    (workspace / "demo.txt").write_text("uno\n")
    _git(root, "add", "workspace/demo.txt")
    _git(root, "-c", "user.name=Test", "-c", "user.email=test@localhost", "commit", "-m", "base")
    (workspace / "demo.txt").write_text("dos\n")
    assert "demo.txt" in git_status(workspace)
    assert "-uno" in git_diff(workspace)
    assert "+dos" in git_diff(workspace)
