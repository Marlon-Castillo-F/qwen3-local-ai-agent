from pathlib import Path


WORKSPACE = (Path.home() / "ai-agent" / "workspace").resolve()


def _safe_path(relative_path: str) -> Path:
    """Resuelve una ruta y garantiza que permanezca dentro del workspace."""

    target = (WORKSPACE / relative_path).resolve()

    try:
        target.relative_to(WORKSPACE)
    except ValueError as exc:
        raise PermissionError(
            "Acceso bloqueado: la ruta está fuera del workspace"
        ) from exc

    return target


def list_files() -> str:
    """Lista archivos y directorios del workspace."""

    WORKSPACE.mkdir(parents=True, exist_ok=True)

    items = sorted(WORKSPACE.iterdir(), key=lambda p: p.name.lower())

    if not items:
        return "El workspace está vacío"

    results = []

    for item in items:
        if item.is_dir():
            results.append(f"[DIR]  {item.name}")
        elif item.is_file():
            results.append(f"[FILE] {item.name}")

    return "\n".join(results)


def read_file(relative_path: str) -> str:
    """Lee un archivo de texto dentro del workspace."""

    target = _safe_path(relative_path)

    if not target.exists():
        return f"ERROR: El archivo no existe: {relative_path}"

    if not target.is_file():
        return f"ERROR: La ruta no es un archivo: {relative_path}"

    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "ERROR: El archivo no parece ser texto UTF-8"
    except OSError as exc:
        return f"ERROR: No se pudo leer el archivo: {exc}"
