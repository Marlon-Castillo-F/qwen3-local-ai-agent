import json
from typing import Any

from app.tools.files import list_files, read_file


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lista los archivos y directorios disponibles dentro del workspace autorizado",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lee un archivo de texto ubicado dentro del workspace autorizado",
            "parameters": {
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "description": "Ruta relativa del archivo dentro del workspace"
                    }
                },
                "required": ["relative_path"],
                "additionalProperties": False
            }
        }
    }
]


def execute_tool(name: str, arguments: Any) -> str:
    """Ejecuta únicamente herramientas explícitamente permitidas."""

    try:
        if isinstance(arguments, str):
            arguments = json.loads(arguments) if arguments else {}

        if name == "list_files":
            return list_files()

        if name == "read_file":
            relative_path = arguments.get("relative_path")

            if not relative_path:
                return "ERROR: Falta relative_path"

            return read_file(relative_path)

        return f"ERROR: Herramienta no permitida: {name}"

    except PermissionError as exc:
        return f"ERROR DE SEGURIDAD: {exc}"

    except json.JSONDecodeError:
        return "ERROR: Los argumentos de la herramienta no son JSON válido"

    except Exception as exc:
        return f"ERROR ejecutando {name}: {exc}"
