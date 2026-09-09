from app.config import Settings
from app.knowledge import KnowledgeIndex
from app.tools.base import ToolRegistry, ToolSpec
from app.tools.dba import (
    analyze_deadlock_xml,
    analyze_execution_plan,
    analyze_statistics_io,
    analyze_statistics_time,
)
from app.tools.files import list_files, read_file, write_file
from app.tools.git_tools import git_diff, git_status
from app.tools.test_tools import run_tests


def build_registry(
    settings: Settings,
    *,
    knowledge_index: KnowledgeIndex | None = None,
) -> ToolRegistry:
    registry = ToolRegistry(max_result_chars=settings.max_tool_result_chars)
    index = knowledge_index or KnowledgeIndex(settings.knowledge_dir, settings.knowledge_db)
    if knowledge_index is None:
        index.rebuild()
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
    registry.register(
        ToolSpec(
            name="search_knowledge",
            description=(
                "Busca conocimiento técnico SQL Server en el corpus DBA local autorizado. "
                "Úsala antes de afirmar que consultaste documentación especializada."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer"},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            handler=lambda query, top_k=5: index.search(query, top_k),
        )
    )
    for name, description, handler in (
        (
            "analyze_statistics_io",
            "Extrae hechos estructurados de una salida SET STATISTICS IO proporcionada como texto o archivo del workspace.",
            analyze_statistics_io,
        ),
        (
            "analyze_statistics_time",
            "Extrae CPU time y elapsed time de una salida SET STATISTICS TIME proporcionada como texto o archivo del workspace.",
            analyze_statistics_time,
        ),
    ):
        registry.register(
            ToolSpec(
                name=name,
                description=description,
                parameters={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "relative_path": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                handler=lambda text=None, relative_path=None, selected=handler: selected(
                    text=text,
                    relative_path=relative_path,
                    workspace=settings.workspace,
                    max_bytes=settings.max_file_bytes,
                ),
            )
        )
    registry.register(
        ToolSpec(
            name="analyze_execution_plan",
            description="Extrae hechos de un Actual o Estimated Execution Plan .sqlplan XML dentro del workspace.",
            parameters={
                "type": "object",
                "properties": {"relative_path": {"type": "string"}},
                "required": ["relative_path"],
                "additionalProperties": False,
            },
            handler=lambda relative_path: analyze_execution_plan(
                relative_path,
                workspace=settings.workspace,
                max_bytes=settings.max_file_bytes,
            ),
        )
    )
    registry.register(
        ToolSpec(
            name="analyze_deadlock_xml",
            description="Extrae víctima, procesos, recursos y locks de un deadlock XML o XDL dentro del workspace.",
            parameters={
                "type": "object",
                "properties": {"relative_path": {"type": "string"}},
                "required": ["relative_path"],
                "additionalProperties": False,
            },
            handler=lambda relative_path: analyze_deadlock_xml(
                relative_path,
                workspace=settings.workspace,
                max_bytes=settings.max_file_bytes,
            ),
        )
    )
    return registry


__all__ = ["ToolRegistry", "ToolSpec", "build_registry"]
