from __future__ import annotations

import os
import tempfile
from pathlib import Path


DEFAULT_MAX_BYTES = 1024 * 1024


def _root(workspace: Path) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace.resolve(strict=True)


def _safe_path(relative_path: str, *, workspace: Path) -> Path:
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise ValueError("La ruta relativa está vacía")
    if "\x00" in relative_path:
        raise PermissionError("Ruta bloqueada: contiene un byte nulo")
    supplied = Path(relative_path)
    if supplied.is_absolute():
        raise PermissionError("Ruta bloqueada: debe ser relativa al workspace")

    root = _root(workspace)
    unresolved = root / supplied
    current = root
    for part in supplied.parts:
        if part in ("", "."):
            continue
        current = current / part
        if current.is_symlink():
            raise PermissionError("Ruta bloqueada: no se permiten enlaces simbólicos")

    target = unresolved.resolve(strict=False)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise PermissionError("Acceso bloqueado: ruta fuera del workspace") from exc
    return target


def list_files(relative_path: str = ".", *, workspace: Path) -> str:
    target = _safe_path(relative_path, workspace=workspace)
    if not target.exists():
        raise FileNotFoundError(f"El directorio no existe: {relative_path}")
    if not target.is_dir():
        raise ValueError(f"La ruta no es un directorio: {relative_path}")

    items = sorted(target.iterdir(), key=lambda path: path.name.casefold())
    if not items:
        return "El directorio está vacío"
    output: list[str] = []
    for item in items:
        if item.is_symlink():
            output.append(f"[SYMLINK] {item.name} (acceso bloqueado)")
        elif item.is_dir():
            output.append(f"[DIR] {item.name}")
        elif item.is_file():
            output.append(f"[FILE] {item.name}")
    return "\n".join(output)


def read_file(
    relative_path: str,
    *,
    workspace: Path,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> str:
    target = _safe_path(relative_path, workspace=workspace)
    if not target.exists():
        raise FileNotFoundError(f"El archivo no existe: {relative_path}")
    if not target.is_file():
        raise ValueError(f"La ruta no es un archivo: {relative_path}")
    size = target.stat().st_size
    if size > max_bytes:
        raise ValueError(f"Archivo demasiado grande: {size} bytes (máximo {max_bytes})")
    data = target.read_bytes()
    if b"\x00" in data:
        raise ValueError("El archivo parece binario")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("El archivo no es texto UTF-8 válido") from exc


def write_file(
    relative_path: str,
    content: str,
    *,
    workspace: Path,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> str:
    if not isinstance(content, str):
        raise ValueError("El contenido debe ser texto")
    encoded = content.encode("utf-8")
    if len(encoded) > max_bytes:
        raise ValueError(
            f"Contenido demasiado grande: {len(encoded)} bytes (máximo {max_bytes})"
        )
    target = _safe_path(relative_path, workspace=workspace)
    if target == _root(workspace):
        raise ValueError("La ruta debe identificar un archivo")
    if target.exists() and not target.is_file():
        raise ValueError("La ruta existente no es un archivo")
    target.parent.mkdir(parents=True, exist_ok=True)
    _safe_path(str(target.parent.relative_to(_root(workspace))), workspace=workspace)

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", dir=target.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as temporary:
            temporary.write(encoded)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.chmod(temporary_name, 0o640)
        os.replace(temporary_name, target)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
    return f"Archivo escrito: {relative_path} ({len(encoded)} bytes)"
