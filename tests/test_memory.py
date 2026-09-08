from pathlib import Path

from app.memory import MemoryStore


def test_sqlite_memory_and_history(tmp_path: Path):
    store = MemoryStore(tmp_path / "data" / "memory.db")
    store.add("session", "user", "hola")
    store.add(
        "session", "tool", "", tool_name="read_file", tool_result="contenido"
    )
    entries = store.history("session")
    assert [entry.role for entry in entries] == ["user", "tool"]
    assert entries[1].tool_name == "read_file"
    assert entries[1].tool_result == "contenido"
    store.close()


def test_sqlite_memory_redacts_obvious_secrets(tmp_path: Path):
    store = MemoryStore(tmp_path / "memory.db")
    store.add(
        "session",
        "user",
        "contraseña=NoGuardar123 token:abc.def Bearer bearer-value",
    )
    stored = store.history("session")[0].content
    assert "NoGuardar123" not in stored
    assert "abc.def" not in stored
    assert "bearer-value" not in stored
    assert stored.count("[REDACTADO]") == 3
    store.close()
