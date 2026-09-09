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


def test_agent_hides_file_analyzers_without_user_path(settings):
    settings.ensure_directories()
    registry = ToolRegistry()
    for name in ("search_knowledge", "analyze_execution_plan", "analyze_deadlock_xml"):
        registry.register(
            ToolSpec(
                name,
                "test",
                {"type": "object", "properties": {}, "additionalProperties": False},
                lambda: "ok",
            )
        )
    client = FakeClient([ChatResponse(content="respuesta conceptual")])
    memory = MemoryStore(settings.memory_db)
    agent = Agent(client, registry, memory, settings)

    agent.run("Explica un Hash Match con spill en un Actual Execution Plan")

    offered = {schema["function"]["name"] for schema in client.observed_tools[0]}
    assert "search_knowledge" in offered
    assert "analyze_execution_plan" not in offered
    assert "analyze_deadlock_xml" not in offered
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
