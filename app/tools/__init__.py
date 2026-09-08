from app.config import Settings
from app.tools.base import ToolRegistry, ToolSpec
from app.tools.files import list_files, read_file, write_file
from app.tools.git_tools import git_diff, git_status
from app.tools.test_tools import run_tests


def build_registry(settings: Settings) -> ToolRegistry:
    registry = ToolRegistry(max_result_chars=settings.max_tool_result_chars)
    registry.register(
        ToolSpec(
            name="list_files",
            description="Lista archivos y directorios reales del workspace autorizado.",
            parameters={
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "description": "Directorio relativo; usa . para la raíz.",
                    }
                },
                "additionalProperties": False,
            },
            handler=lambda relative_path=".": list_files(
                relative_path, workspace=settings.workspace
            ),
        )
    )
    registry.register(
        ToolSpec(
            name="read_file",
            description="Lee un archivo UTF-8 real dentro del workspace autorizado.",
            parameters={
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "description": "Ruta relativa del archivo dentro del workspace.",
                    }
                },
                "required": ["relative_path"],
                "additionalProperties": False,
            },
            handler=lambda relative_path: read_file(
                relative_path,
                workspace=settings.workspace,
                max_bytes=settings.max_file_bytes,
            ),
        )
    )
    registry.register(
        ToolSpec(
            name="write_file",
            description="Escribe texto UTF-8 dentro del workspace autorizado.",
            parameters={
                "type": "object",
                "properties": {
                    "relative_path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["relative_path", "content"],
                "additionalProperties": False,
            },
            handler=lambda relative_path, content: write_file(
                relative_path,
                content,
                workspace=settings.workspace,
                max_bytes=settings.max_file_bytes,
            ),
        )
    )
    registry.register(
        ToolSpec(
            name="git_status",
            description="Consulta el estado Git real del proyecto, sin modificarlo.",
            parameters={
                "type": "object", "properties": {}, "additionalProperties": False
            },
            handler=lambda: git_status(settings.workspace, timeout=30),
        )
    )
    registry.register(
        ToolSpec(
            name="git_diff",
            description="Muestra cambios Git reales staged y unstaged, en modo lectura.",
            parameters={
                "type": "object", "properties": {}, "additionalProperties": False
            },
            handler=lambda: git_diff(settings.workspace, timeout=30),
        )
    )
    registry.register(
        ToolSpec(
            name="run_tests",
            description="Ejecuta pytest mediante una de dos órdenes permitidas, sin shell.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "enum": ["python -m pytest", "pytest"],
                    }
                },
                "additionalProperties": False,
            },
            handler=lambda command="python -m pytest": run_tests(
                command, project_root=settings.workspace.parent, timeout=settings.tool_timeout
            ),
        )
    )
    return registry


__all__ = ["ToolRegistry", "ToolSpec", "build_registry"]
