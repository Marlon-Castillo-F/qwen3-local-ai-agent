from app.main import HELP, _show_history, _show_info
from app.memory import MemoryStore
from app.agent import Agent
from app.tools.base import ToolRegistry


class InfoClient:
    def model_info(self):
        return {"connected": True, "detected_model": "detected-qwen"}


class NoopClient:
    def chat(self, messages, tools):
        raise AssertionError("not called")


def test_help_contains_required_commands():
    for command in ("/info", "/clear", "/help", "/history", "/dba", "/knowledge", "/exit"):
        assert command in HELP


def test_info_output_uses_endpoint_result(settings, capsys):
    _show_info(InfoClient(), settings)
    output = capsys.readouterr().out
    assert "CONECTADO" in output
    assert "detected-qwen" in output


def test_history_output(settings, capsys):
    settings.ensure_directories()
    memory = MemoryStore(settings.memory_db)
    agent = Agent(NoopClient(), ToolRegistry(), memory, settings)
    memory.add(agent.session_id, "user", "hola")
    memory.add(agent.session_id, "assistant", "respuesta")
    _show_history(agent)
    output = capsys.readouterr().out
    assert "Tú> hola" in output
    assert "IA> respuesta" in output
    memory.close()
