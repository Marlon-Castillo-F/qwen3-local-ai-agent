from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Callable
from typing import Any

from app.client import LlamaClient, ModelResponseError
from app.config import SYSTEM_PROMPT, Settings
from app.memory import MemoryEntry, MemoryStore
from app.tools.base import ToolError, ToolRegistry


EventCallback = Callable[[str, str], None]


_FILE_ANALYZER_SUFFIXES = {
    "analyze_execution_plan": (".sqlplan",),
    "analyze_deadlock_xml": (".xml", ".xdl"),
}
_GENERAL_WORKSPACE_TOOLS = {
    "list_files",
    "read_file",
    "write_file",
    "git_status",
    "git_diff",
    "run_tests",
}
_CONTEXT_GATED_TOOLS = (
    set(_FILE_ANALYZER_SUFFIXES)
    | _GENERAL_WORKSPACE_TOOLS
    | {"analyze_statistics_io", "analyze_statistics_time"}
)
_DBA_CONCEPT_TERMS = (
    "sql server",
    "execution plan",
    "plan de ejecución",
    "statistics io",
    "statistics time",
    "hash match",
    "spill",
    "tempdb",
    "index seek",
    "index scan",
    "table scan",
    "key lookup",
    "query store",
    "cardinalidad",
    "deadlock",
)
_WORKSPACE_INTENT_TERMS = (
    "workspace",
    "archivo",
    "fichero",
    "directorio",
    "carpeta",
    "lista los",
    "listar los",
    "qué archivos",
    "que archivos",
    "lee ",
    "leer ",
    "escribe ",
    "git ",
    "pytest",
    "pruebas",
    "tests",
)
_TEXT_PATH = re.compile(r"(?<!\w)[\w./-]+\.txt(?!\w)", re.IGNORECASE)
_POSITIVE_SCAN_INFERENCE = re.compile(
    r"(?<!no )\b(?:indica(?:\s+que)?|significa(?:\s+que)?|confirma(?:\s+que)?|"
    r"hubo|se realizó|ejecutó)\b.{0,100}\bescaneo\b",
    re.IGNORECASE | re.DOTALL,
)


def _contains_statistics_io_payload(user_input: str) -> bool:
    folded = user_input.casefold()
    return bool(_TEXT_PATH.search(user_input)) or (
        "table '" in folded
        and any(
            metric in folded
            for metric in ("scan count", "logical reads", "physical reads", "read-ahead reads")
        )
    )


def _contains_statistics_time_payload(user_input: str) -> bool:
    folded = user_input.casefold()
    return bool(_TEXT_PATH.search(user_input)) or (
        "cpu time" in folded and "elapsed time" in folded
    )


def _is_conceptual_dba_request(user_input: str) -> bool:
    folded = user_input.casefold()
    return any(term in folded for term in _DBA_CONCEPT_TERMS) and not any(
        term in folded for term in _WORKSPACE_INTENT_TERMS
    )


def _grounding_correction(user_input: str, answer: str) -> str | None:
    request = user_input.casefold()
    response = answer.casefold()
    if (
        "statistics io" in request
        and "scan count" in request
        and _POSITIVE_SCAN_INFERENCE.search(answer)
    ):
        return (
            "Corrige la respuesta antes de entregarla. Has inferido o parafraseado "
            "scan count como un escaneo. STATISTICS IO no prueba que hubiera Table "
            "Scan, Index Scan, Index Seek, Key Lookup ni una operación genérica de "
            "escaneo. Conserva las métricas observadas y di que el operador solo puede "
            "identificarse con evidencia del plan de ejecución."
        )
    if "actual execution plan" in request and "spill" in request:
        has_estimated_distinction = (
            "showplan_xml" in response
            and "estimad" in response
            and ("no ejecuta" in response or "sin ejecutar" in response)
        )
        if not has_estimated_distinction:
            return (
                "Corrige la respuesta antes de entregarla. Distingue explícitamente "
                "que SET SHOWPLAN_XML ON y Estimated Execution Plan en SSMS son "
                "estimados y no ejecutan la consulta. Para un plan real menciona "
                "Include Actual Execution Plan (Ctrl+M), SET STATISTICS XML ON o, "
                "cuando sea apropiado, SET STATISTICS PROFILE ON. Mantén causas como "
                "hipótesis y no deduzcas falta de índices ni memoria del servidor solo "
                "por el spill."
            )
    return None


def _metric_value(user_input: str, label: str) -> str:
    match = re.search(rf"\b{re.escape(label)}\s+(\d+)\b", user_input, re.IGNORECASE)
    return match.group(1) if match else "no indicado"


def _grounding_fallback(user_input: str) -> str:
    request = user_input.casefold()
    if "statistics io" in request and "scan count" in request:
        scan_count = _metric_value(user_input, "scan count")
        logical_reads = _metric_value(user_input, "logical reads")
        physical_reads = _metric_value(user_input, "physical reads")
        read_ahead_reads = _metric_value(user_input, "read-ahead reads")
        return (
            "Hechos observados en STATISTICS IO: "
            f"scan count={scan_count}, logical reads={logical_reads}, "
            f"physical reads={physical_reads} y read-ahead reads={read_ahead_reads}. "
            "Las logical reads cuentan accesos a páginas en el buffer pool. "
            "Physical reads=0 indica que esa salida no reportó lecturas físicas "
            "sincrónicas para la ejecución; no demuestra por sí solo eficiencia. "
            "Read-ahead reads=0 solo informa que no se reportaron lecturas anticipadas. "
            "Scan count es una métrica de STATISTICS IO y no identifica el operador "
            "físico. Con estos datos no puede afirmarse Table Scan, Index Scan, Index "
            "Seek, Key Lookup ni la ausencia de alguno de ellos. Para identificar el "
            "operador se necesita evidencia del plan de ejecución; para valorar el "
            "rendimiento también hacen falta duración, CPU, filas y contexto de carga."
        )
    return (
        "Hecho observado: el Actual Execution Plan informa que el Hash Match derramó "
        "trabajo intermedio a tempdb durante esa ejecución. Esto indica que el operador "
        "no completó todo su trabajo dentro de la memoria de trabajo concedida, pero no "
        "demuestra por sí solo falta de memoria del servidor, estadísticas obsoletas, "
        "un índice faltante ni la causa raíz. Como hipótesis deben evaluarse diferencias "
        "entre filas estimadas y reales, ancho de fila, sesgo de datos, volumen de "
        "entrada, grant solicitado/concedido/usado, presión concurrente y límites del "
        "grant. Antes de cambiar memoria, índices o consulta, revisa los detalles y nivel "
        "del spill, MemoryGrantInfo, Estimated Rows frente a Actual Rows, ejecuciones del "
        "operador, STATISTICS IO/TIME, concurrencia, esperas y el historial de Query "
        "Store. Distinción de captura: SET SHOWPLAN_XML ON o Estimated Execution Plan "
        "en SSMS producen un plan estimado y no ejecutan la consulta. Para un plan real, "
        "usa Include Actual Execution Plan en SSMS (Ctrl+M), SET STATISTICS XML ON o, "
        "cuando resulte apropiado, SET STATISTICS PROFILE ON."
    )


class Agent:
    def __init__(
        self,
        client: LlamaClient,
        registry: ToolRegistry,
        memory: MemoryStore,
        settings: Settings,
        *,
        logger: logging.Logger | None = None,
    ):
        self.client = client
        self.registry = registry
        self.memory = memory
        self.settings = settings
        self.logger = logger or logging.getLogger("ai_agent.agent")
        self.session_id = ""
        self.messages: list[dict[str, Any]] = []
        self.clear()

    def clear(self) -> None:
        self.session_id = str(uuid.uuid4())
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.logger.info("session_started session_id=%s", self.session_id)

    def history(self) -> list[MemoryEntry]:
        return self.memory.history(self.session_id)

    def _tool_schemas_for(self, user_input: str) -> list[dict[str, Any]]:
        """Expose tools only when the current request supplies their input or intent."""
        normalized_input = user_input.casefold()
        conceptual_dba = _is_conceptual_dba_request(user_input)
        schemas: list[dict[str, Any]] = []
        for schema in self.registry.schemas():
            name = schema["function"]["name"]
            suffixes = _FILE_ANALYZER_SUFFIXES.get(name)
            if suffixes and not any(
                suffix in normalized_input for suffix in suffixes
            ):
                continue
            if name == "analyze_statistics_io" and not _contains_statistics_io_payload(
                user_input
            ):
                continue
            if name == "analyze_statistics_time" and not _contains_statistics_time_payload(
                user_input
            ):
                continue
            if conceptual_dba and name in _GENERAL_WORKSPACE_TOOLS:
                continue
            schemas.append(schema)
        return schemas

    def run(self, user_input: str, on_event: EventCallback | None = None) -> str:
        on_event = on_event or (lambda _kind, _value: None)
        self.messages.append({"role": "user", "content": user_input})
        self.memory.add(self.session_id, "user", user_input)
        tool_schemas = self._tool_schemas_for(user_input)
        offered_tool_names = {
            schema["function"]["name"] for schema in tool_schemas
        }
        grounding_retries = 0

        for _round in range(self.settings.max_tool_rounds + 1):
            response = self.client.chat(self.messages, tool_schemas)
            if not response.tool_calls:
                if not response.content.strip():
                    raise ModelResponseError("El modelo devolvió una respuesta vacía")
                correction = _grounding_correction(user_input, response.content)
                if correction:
                    if grounding_retries >= 1:
                        content = _grounding_fallback(user_input)
                        self.logger.warning(
                            "response_grounding_fallback session_id=%s", self.session_id
                        )
                        on_event("response_fallback", content)
                        self.messages.append({"role": "assistant", "content": content})
                        self.memory.add(self.session_id, "assistant", content)
                        return content
                    grounding_retries += 1
                    self.logger.warning(
                        "response_grounding_retry session_id=%s", self.session_id
                    )
                    on_event("response_retry", correction)
                    self.messages.extend(
                        [
                            {"role": "assistant", "content": response.content},
                            {"role": "user", "content": correction},
                        ]
                    )
                    continue
                self.messages.append(
                    {"role": "assistant", "content": response.content}
                )
                self.memory.add(self.session_id, "assistant", response.content)
                return response.content

            assistant_message: dict[str, Any] = {
                "role": "assistant",
                "content": response.content or "",
                "tool_calls": [call.as_openai_dict() for call in response.tool_calls],
            }
            self.messages.append(assistant_message)
            if response.content:
                self.memory.add(self.session_id, "assistant", response.content)

            for call in response.tool_calls:
                on_event("tool_call", call.name)
                self.logger.info(
                    "tool_requested session_id=%s name=%s", self.session_id, call.name
                )
                try:
                    if (
                        call.name in _CONTEXT_GATED_TOOLS
                        and call.name not in offered_tool_names
                    ):
                        raise ToolError(
                            "Herramienta no disponible para el contexto y la evidencia "
                            "aportados por el usuario"
                        )
                    result = self.registry.execute(call.name, call.arguments)
                except ToolError as exc:
                    result = f"ERROR: {exc}"
                on_event("tool_result", result)
                self.memory.add(
                    self.session_id,
                    "tool",
                    "",
                    tool_name=call.name,
                    tool_result=result,
                )
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": call.name,
                        "content": result,
                    }
                )

        raise ModelResponseError(
            f"Se alcanzó el límite de {self.settings.max_tool_rounds} rondas de herramientas"
        )
