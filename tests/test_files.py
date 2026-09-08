from pathlib import Path

import pytest

from app.tools.files import list_files, read_file, write_file


def test_list_files_and_read_file(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "directorio").mkdir()
    (workspace / "prueba.txt").write_text("Servidor de IA local\n", encoding="utf-8")
    listing = list_files(workspace=workspace)
    assert "[DIR] directorio" in listing
    assert "[FILE] prueba.txt" in listing
    assert read_file("prueba.txt", workspace=workspace) == "Servidor de IA local\n"


def test_write_file_is_atomic_and_nested(tmp_path: Path):
    workspace = tmp_path / "workspace"
    result = write_file("nested/demo.txt", "contenido", workspace=workspace)
    assert "Archivo escrito" in result
    assert (workspace / "nested" / "demo.txt").read_text() == "contenido"


@pytest.mark.parametrize("path", ["../../etc/passwd", "/etc/passwd"])
def test_path_traversal_is_blocked(tmp_path: Path, path: str):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    with pytest.raises(PermissionError):
        read_file(path, workspace=workspace)


def test_symlink_escape_is_blocked(tmp_path: Path):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    (outside / "secret.txt").write_text("secreto")
    try:
        (workspace / "escape").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("El sistema no permite crear symlinks")
    with pytest.raises(PermissionError):
        read_file("escape/secret.txt", workspace=workspace)
    with pytest.raises(PermissionError):
        write_file("escape/new.txt", "no", workspace=workspace)


def test_missing_file(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    with pytest.raises(FileNotFoundError):
        read_file("missing.txt", workspace=workspace)


def test_binary_file_is_blocked(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "binary.bin").write_bytes(b"abc\x00def")
    with pytest.raises(ValueError, match="binario"):
        read_file("binary.bin", workspace=workspace)


def test_large_file_is_blocked(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "large.txt").write_text("x" * 20)
    with pytest.raises(ValueError, match="demasiado grande"):
        read_file("large.txt", workspace=workspace, max_bytes=10)
    with pytest.raises(ValueError, match="demasiado grande"):
        write_file("other.txt", "x" * 20, workspace=workspace, max_bytes=10)
