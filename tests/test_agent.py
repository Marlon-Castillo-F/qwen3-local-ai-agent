from pathlib import Path

from app.agent import Agent
from app.memory import MemoryStore
from app.models import ChatResponse, ToolCall
from app.tools.base import ToolRegistry, ToolSpec


class FakeClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.observed_messages = []
        self.observed_tools = []

    def chat(self, messages, tools):
        self.observed_messages.append(list(messages))
        self.observed_tools.append(list(tools))
        return next(self.responses)


def test_agent_executes_real_registered_tool_and_returns_result(settings):
    settings.ensure_directories()
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            "list_files",
            "lista",
            {"type": "object", "properties": {}, "additionalProperties": False},
            lambda: "[FILE] real.txt",
        )
    )
    client = FakeClient(
        [
            ChatResponse(tool_calls=[ToolCall("call-1", "list_files", "{}")] ),
            ChatResponse(content="Está disponible real.txt"),
        ]
    )
    memory = MemoryStore(settings.memory_db)
    agent = Agent(client, registry, memory, settings)
    events = []
    answer = agent.run("lista", lambda kind, value: events.append((kind, value)))
    assert answer == "Está disponible real.txt"
    assert ("tool_call", "list_files") in events
    assert ("tool_result", "[FILE] real.txt") in events
    assert client.observed_messages[1][-1]["role"] == "tool"
    assert client.observed_messages[1][-1]["content"] == "[FILE] real.txt"
    assert [item.role for item in agent.history()] == ["user", "tool", "assistant"]
    memory.close()


def test_agent_rejects_unregistered_tool(settings):
    settings.ensure_directories()
    client = FakeClient(
        [
            ChatResponse(tool_calls=[ToolCall("bad", "sudo", "{}")] ),
            ChatResponse(content="La acción fue bloqueada"),
        ]
    )
    memory = MemoryStore(settings.memory_db)
    agent = Agent(client, ToolRegistry(), memory, settings)
    assert agent.run("haz sudo") == "La acción fue bloqueada"
    assert "no permitida" in client.observed_messages[1][-1]["content"]
    memory.close()


def test_clear_starts_empty_history(settings):
    settings.ensure_directories()
    memory = MemoryStore(settings.memory_db)
    agent = Agent(FakeClient([ChatResponse(content="hola")]), ToolRegistry(), memory, settings)
    agent.run("hola")
    old_session = agent.session_id
    agent.clear()
    assert agent.session_id != old_session
    assert agent.history() == []
    assert len(agent.messages) == 1
    memory.close()


def test_agent_hides_unrelated_tools_for_conceptual_dba_request(settings):
    settings.ensure_directories()
    registry = ToolRegistry()
    for name in (
        "search_knowledge",
        "list_files",
        "analyze_statistics_io",
        "analyze_execution_plan",
        "analyze_deadlock_xml",
    ):
        registry.register(
            ToolSpec(
                name,
                "test",
                {"type": "object", "properties": {}, "additionalProperties": False},
                lambda: "ok",
            )
        )
    client = FakeClient(
        [
            ChatResponse(
                content=(
                    "SHOWPLAN_XML es un plan estimado y no ejecuta la consulta; "
                    "Ctrl+M permite obtener el plan real."
                )
            )
        ]
    )
    memory = MemoryStore(settings.memory_db)
    agent = Agent(client, registry, memory, settings)

    agent.run("Explica un Hash Match con spill en un Actual Execution Plan")

    offered = {schema["function"]["name"] for schema in client.observed_tools[0]}
    assert offered == {"search_knowledge"}
    memory.close()


def test_agent_exposes_matching_file_analyzer_for_explicit_path(settings):
    settings.ensure_directories()
    registry = ToolRegistry()
    for name in ("analyze_execution_plan", "analyze_deadlock_xml"):
        registry.register(
            ToolSpec(
                name,
                "test",
                {"type": "object", "properties": {}, "additionalProperties": False},
                lambda: "ok",
            )
        )
    client = FakeClient([ChatResponse(content="analizaré el archivo")])
    memory = MemoryStore(settings.memory_db)
    agent = Agent(client, registry, memory, settings)

    agent.run("Analiza workspace/dba-samples/sample.sqlplan")

    offered = {schema["function"]["name"] for schema in client.observed_tools[0]}
    assert "analyze_execution_plan" in offered
    assert "analyze_deadlock_xml" not in offered
    memory.close()


def test_agent_exposes_statistics_io_only_for_parseable_payload(settings):
    settings.ensure_directories()
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            "analyze_statistics_io",
            "test",
            {"type": "object", "properties": {}, "additionalProperties": False},
            lambda: "ok",
        )
    )
    memory = MemoryStore(settings.memory_db)

    conceptual_client = FakeClient([ChatResponse(content="respuesta conceptual")])
    Agent(conceptual_client, registry, memory, settings).run(
        "STATISTICS IO muestra Scan count 1 y logical reads 120000. ¿Qué significa?"
    )
    assert conceptual_client.observed_tools[0] == []

    payload_client = FakeClient([ChatResponse(content="respuesta basada en datos")])
    Agent(payload_client, registry, memory, settings).run(
        "Table 'Orders'. Scan count 1, logical reads 120000."
    )
    offered = {
        schema["function"]["name"] for schema in payload_client.observed_tools[0]
    }
    assert offered == {"analyze_statistics_io"}
    memory.close()


def test_agent_keeps_workspace_tool_for_explicit_file_intent(settings):
    settings.ensure_directories()
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            "list_files",
            "test",
            {"type": "object", "properties": {}, "additionalProperties": False},
            lambda: "ok",
        )
    )
    client = FakeClient([ChatResponse(content="respuesta")])
    memory = MemoryStore(settings.memory_db)

    Agent(client, registry, memory, settings).run(
        "¿Qué archivos hay disponibles en el workspace?"
    )

    offered = {schema["function"]["name"] for schema in client.observed_tools[0]}
    assert offered == {"list_files"}
    memory.close()


def test_agent_retries_positive_scan_count_inference(settings):
    settings.ensure_directories()
    client = FakeClient(
        [
            ChatResponse(content="Scan count indica que se realizó un escaneo lógico."),
            ChatResponse(
                content=(
                    "Scan count es una métrica observada; no identifica operadores. "
                    "El plan de ejecución es la evidencia necesaria."
                )
            ),
        ]
    )
    memory = MemoryStore(settings.memory_db)
    retries = []

    answer = Agent(client, ToolRegistry(), memory, settings).run(
        "STATISTICS IO muestra Scan count 1.",
        lambda kind, value: retries.append((kind, value)),
    )

    assert "no identifica operadores" in answer
    assert len(client.observed_messages) == 2
    assert retries[0][0] == "response_retry"
    memory.close()


def test_agent_retries_spill_answer_without_plan_capture_distinction(settings):
    settings.ensure_directories()
    client = FakeClient(
        [
            ChatResponse(content="El spill usó tempdb; revisa el memory grant."),
            ChatResponse(
                content=(
                    "SHOWPLAN_XML es estimado y no ejecuta la consulta. Para el plan "
                    "real usa Ctrl+M o SET STATISTICS XML ON."
                )
            ),
        ]
    )
    memory = MemoryStore(settings.memory_db)

    answer = Agent(client, ToolRegistry(), memory, settings).run(
        "Un Actual Execution Plan muestra un spill.",
    )

    assert "SHOWPLAN_XML es estimado" in answer
    assert len(client.observed_messages) == 2
    memory.close()


def test_agent_falls_back_after_repeated_scan_count_inference(settings):
    settings.ensure_directories()
    client = FakeClient(
        [
            ChatResponse(content="Scan count indica que se realizó un escaneo."),
            ChatResponse(content="Scan count confirma que hubo un escaneo."),
        ]
    )
    memory = MemoryStore(settings.memory_db)

    answer = Agent(client, ToolRegistry(), memory, settings).run(
        "STATISTICS IO: Scan count 1, logical reads 120000, physical reads 0 y "
        "read-ahead reads 0."
    )

    assert "scan count=1" in answer.casefold()
    assert "no identifica el operador físico" in answer
    assert "no puede afirmarse Table Scan" in answer
    assert len(client.observed_messages) == 2
    memory.close()


def test_agent_falls_back_after_repeated_spill_capture_error(settings):
    settings.ensure_directories()
    client = FakeClient(
        [
            ChatResponse(content="El spill usó tempdb."),
            ChatResponse(content="Revisa el plan real con SHOWPLAN_XML."),
        ]
    )
    memory = MemoryStore(settings.memory_db)

    answer = Agent(client, ToolRegistry(), memory, settings).run(
        "Un Actual Execution Plan muestra un Hash Match con spill a tempdb."
    )

    assert "plan estimado y no ejecutan la consulta" in answer
    assert "Include Actual Execution Plan" in answer
    assert "SET STATISTICS XML ON" in answer
    assert "SET STATISTICS PROFILE ON" in answer
    memory.close()
