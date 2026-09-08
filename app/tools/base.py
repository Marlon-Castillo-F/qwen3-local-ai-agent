from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable


class ToolError(RuntimeError):
    pass


class ToolNotAllowedError(ToolError):
    pass


class ToolValidationError(ToolError):
    pass


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., str]

    def openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(self, *, max_result_chars: int = 64 * 1024):
        self._tools: dict[str, ToolSpec] = {}
        self.max_result_chars = max_result_chars
        self.logger = logging.getLogger("ai_agent.tools")

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Herramienta duplicada: {spec.name}")
        self._tools[spec.name] = spec

    def schemas(self) -> list[dict[str, Any]]:
        return [spec.openai_schema() for spec in self._tools.values()]

    def execute(self, name: str, arguments: str | dict[str, Any]) -> str:
        started = time.monotonic()
        spec = self._tools.get(name)
        if spec is None:
            self.logger.warning("tool_blocked name=%r reason=not_allowed", name)
            raise ToolNotAllowedError(f"Herramienta no permitida: {name}")

        parsed = self._parse_arguments(arguments)
        self._validate(parsed, spec.parameters)
        self.logger.info("tool_accepted name=%s", name)
        try:
            result = str(spec.handler(**parsed))
        except (PermissionError, FileNotFoundError, ValueError, TimeoutError) as exc:
            self.logger.warning(
                "tool_blocked name=%s reason=%s", name, type(exc).__name__
            )
            raise ToolError(str(exc)) from exc
        except Exception as exc:
            self.logger.exception("tool_failed name=%s", name)
            raise ToolError(f"Error ejecutando {name}: {type(exc).__name__}") from exc

        if len(result) > self.max_result_chars:
            result = result[: self.max_result_chars] + "\n[resultado truncado]"
        self.logger.info(
            "tool_result name=%s chars=%d duration=%.3fs",
            name,
            len(result),
            time.monotonic() - started,
        )
        return result

    @staticmethod
    def _parse_arguments(arguments: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments or "{}")
            except json.JSONDecodeError as exc:
                raise ToolValidationError("Argumentos JSON inválidos") from exc
        if not isinstance(arguments, dict):
            raise ToolValidationError("Los argumentos deben ser un objeto JSON")
        return arguments

    @staticmethod
    def _validate(arguments: dict[str, Any], schema: dict[str, Any]) -> None:
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for key in required:
            if key not in arguments:
                raise ToolValidationError(f"Falta el argumento requerido: {key}")
        if schema.get("additionalProperties") is False:
            extras = set(arguments) - set(properties)
            if extras:
                raise ToolValidationError(
                    "Argumentos no permitidos: " + ", ".join(sorted(extras))
                )
        expected_types = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "object": dict,
            "array": list,
        }
        for key, value in arguments.items():
            rule = properties.get(key, {})
            expected = expected_types.get(rule.get("type"))
            if expected is not None and not isinstance(value, expected):
                raise ToolValidationError(f"Tipo inválido para {key}")
            if "enum" in rule and value not in rule["enum"]:
                raise ToolValidationError(f"Valor no permitido para {key}")
