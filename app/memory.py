from __future__ import annotations

import sqlite3
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(password|passwd|contraseña|token|api[_ -]?key|secret)"
    r"(\s*[:=]\s*)([^\s,;]+)"
)
_BEARER_TOKEN = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_PRIVATE_KEY = re.compile(
    r"-----BEGIN [^-\n]*PRIVATE KEY-----.*?-----END [^-\n]*PRIVATE KEY-----",
    re.DOTALL,
)


def redact_sensitive(value: str | None) -> str | None:
    if value is None:
        return None
    value = _PRIVATE_KEY.sub("[CLAVE PRIVADA REDACTADA]", value)
    value = _BEARER_TOKEN.sub("Bearer [REDACTADO]", value)
    return _SECRET_ASSIGNMENT.sub(r"\1\2[REDACTADO]", value)


@dataclass(frozen=True)
class MemoryEntry:
    timestamp: str
    role: str
    content: str
    tool_name: str | None = None
    tool_result: str | None = None


class MemoryStore:
    def __init__(self, database: Path):
        database.parent.mkdir(parents=True, exist_ok=True)
        self.database = database
        self.connection = sqlite3.connect(database)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_name TEXT,
                tool_result TEXT
            )
            """
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_session "
            "ON messages(session_id, id)"
        )
        self.connection.commit()

    def add(
        self,
        session_id: str,
        role: str,
        content: str,
        *,
        tool_name: str | None = None,
        tool_result: str | None = None,
    ) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        self.connection.execute(
            """
            INSERT INTO messages
                (session_id, timestamp, role, content, tool_name, tool_result)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                timestamp,
                role,
                redact_sensitive(content) or "",
                tool_name,
                redact_sensitive(tool_result),
            ),
        )
        self.connection.commit()

    def history(self, session_id: str) -> list[MemoryEntry]:
        rows = self.connection.execute(
            """
            SELECT timestamp, role, content, tool_name, tool_result
            FROM messages WHERE session_id = ? ORDER BY id
            """,
            (session_id,),
        ).fetchall()
        return [MemoryEntry(**dict(row)) for row in rows]

    def close(self) -> None:
        self.connection.close()
