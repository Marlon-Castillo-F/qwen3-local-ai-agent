import json
from pathlib import Path

import pytest

from app.knowledge import KnowledgeIndex


def _document(title: str, topic: str, body: str) -> str:
    return f"""---
title: {title}
topic: {topic}
source: https://learn.microsoft.com/example
consulted: 2026-09-09
---

## Summary

{body}
"""


def test_indexes_and_retrieves_corpus(tmp_path: Path):
    root = tmp_path / "knowledge"
    root.mkdir()
    (root / "indexing.md").write_text(
        _document("Index design", "indexing", "Key Lookup selectivity covering index."),
        encoding="utf-8",
    )
    (root / "backup.md").write_text(
        _document("Backup chain", "backup-restore", "Point-in-time log chain STOPAT."),
        encoding="utf-8",
    )
    index = KnowledgeIndex(root, tmp_path / "knowledge.db")
    assert index.rebuild() == 2
    result = json.loads(index.search("key lookup covering", top_k=1))
    assert result["results"][0]["document"] == "indexing.md"
    assert result["results"][0]["source"].startswith("https://learn.microsoft.com/")
    assert index.stats() == {
        "documents": 2,
        "categories": ["backup-restore", "indexing"],
    }


def test_search_with_no_match_returns_empty_results(tmp_path: Path):
    root = tmp_path / "knowledge"
    root.mkdir()
    (root / "one.md").write_text(
        _document("One", "test", "cardinality statistics"), encoding="utf-8"
    )
    index = KnowledgeIndex(root, tmp_path / "knowledge.db")
    index.rebuild()
    assert json.loads(index.search("deadlock"))["results"] == []


@pytest.mark.parametrize("query", ["", "  ", "   "])
def test_empty_query_is_rejected(tmp_path: Path, query):
    root = tmp_path / "knowledge"
    root.mkdir()
    index = KnowledgeIndex(root, tmp_path / "knowledge.db")
    index.rebuild()
    with pytest.raises(ValueError, match="vacía"):
        index.search(query)


def test_missing_corpus_is_reported(tmp_path: Path):
    index = KnowledgeIndex(tmp_path / "missing", tmp_path / "knowledge.db")
    with pytest.raises(FileNotFoundError):
        index.rebuild()


def test_invalid_document_metadata_is_rejected(tmp_path: Path):
    root = tmp_path / "knowledge"
    root.mkdir()
    (root / "bad.md").write_text("sin metadatos", encoding="utf-8")
    with pytest.raises(ValueError, match="metadatos"):
        KnowledgeIndex(root, tmp_path / "knowledge.db").rebuild()
