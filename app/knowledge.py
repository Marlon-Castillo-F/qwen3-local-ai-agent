from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_TOKEN = re.compile(r"[\w][\w.+#-]*", re.UNICODE)


@dataclass(frozen=True)
class KnowledgeDocument:
    path: str
    title: str
    topic: str
    source: str
    body: str


def _parse_document(path: Path, root: Path, *, max_bytes: int) -> KnowledgeDocument:
    if path.is_symlink():
        raise PermissionError(f"Documento de conocimiento bloqueado por symlink: {path.name}")
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"Documento demasiado grande: {path.name} ({size} bytes)")
    text = path.read_text(encoding="utf-8")
    match = _FRONT_MATTER.match(text)
    if not match:
        raise ValueError(f"Documento sin metadatos YAML simples: {path.name}")
    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip('"')
    for required in ("title", "topic", "source"):
        if not metadata.get(required):
            raise ValueError(f"Falta {required} en {path.name}")
    return KnowledgeDocument(
        path=path.relative_to(root).as_posix(),
        title=metadata["title"],
        topic=metadata["topic"],
        source=metadata["source"],
        body=text[match.end() :].strip(),
    )


class KnowledgeIndex:
    def __init__(
        self,
        knowledge_root: Path,
        database: Path,
        *,
        max_document_bytes: int = 256 * 1024,
    ):
        self.knowledge_root = knowledge_root
        self.database = database
        self.max_document_bytes = max_document_bytes

    def _connect(self) -> sqlite3.Connection:
        self.database.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database)
        try:
            connection.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS documents USING fts5(
                    path UNINDEXED,
                    title,
                    topic,
                    source UNINDEXED,
                    body,
                    tokenize='unicode61 remove_diacritics 2'
                )
                """
            )
        except sqlite3.OperationalError as exc:
            connection.close()
            raise RuntimeError("SQLite FTS5 no está disponible") from exc
        return connection

    def rebuild(self) -> int:
        root = self.knowledge_root.resolve(strict=True)
        documents: list[KnowledgeDocument] = []
        for path in sorted(root.rglob("*.md")):
            resolved = path.resolve(strict=True)
            try:
                resolved.relative_to(root)
            except ValueError as exc:
                raise PermissionError("Documento fuera del corpus autorizado") from exc
            documents.append(
                _parse_document(path, root, max_bytes=self.max_document_bytes)
            )
        connection = self._connect()
        try:
            with connection:
                connection.execute("DELETE FROM documents")
                connection.executemany(
                    "INSERT INTO documents(path, title, topic, source, body) VALUES (?, ?, ?, ?, ?)",
                    [
                        (document.path, document.title, document.topic, document.source, document.body)
                        for document in documents
                    ],
                )
        finally:
            connection.close()
        return len(documents)

    @staticmethod
    def _match_expression(query: str) -> str:
        terms = _TOKEN.findall(query.casefold())
        if not terms:
            raise ValueError("La consulta de conocimiento está vacía")
        unique = list(dict.fromkeys(terms))[:20]
        return " OR ".join(f'"{term.replace(chr(34), "")}"*' for term in unique)

    def search(self, query: str, top_k: int = 5) -> str:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("La consulta de conocimiento está vacía")
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 10:
            raise ValueError("top_k debe estar entre 1 y 10")
        expression = self._match_expression(query)
        connection = self._connect()
        try:
            rows = connection.execute(
                """
                SELECT path, title, topic, source,
                       snippet(documents, 4, '[', ']', ' … ', 32),
                       bm25(documents)
                FROM documents
                WHERE documents MATCH ?
                ORDER BY bm25(documents)
                LIMIT ?
                """,
                (expression, top_k),
            ).fetchall()
        finally:
            connection.close()
        results = [
            {
                "document": row[0],
                "title": row[1],
                "topic": row[2],
                "source": row[3],
                "fragment": row[4],
                "score": round(-float(row[5]), 6),
            }
            for row in rows
        ]
        return json.dumps({"query": query, "results": results}, ensure_ascii=False, indent=2)

    def stats(self) -> dict[str, Any]:
        connection = self._connect()
        try:
            count = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            categories = [
                row[0]
                for row in connection.execute(
                    "SELECT DISTINCT topic FROM documents ORDER BY topic"
                ).fetchall()
            ]
        finally:
            connection.close()
        return {"documents": count, "categories": categories}
