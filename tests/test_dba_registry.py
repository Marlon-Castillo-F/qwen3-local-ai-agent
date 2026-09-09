import json
from pathlib import Path

import pytest

from app.knowledge import KnowledgeIndex
from app.tools import build_registry
from app.tools.base import ToolValidationError


def _index(settings) -> KnowledgeIndex:
    settings.knowledge_dir.mkdir(parents=True)
    (settings.knowledge_dir / "test.md").write_text(
        """---
title: Test cardinality
topic: statistics
source: https://learn.microsoft.com/example
---
Cardinality estimation and statistics histogram.
""",
        encoding="utf-8",
    )
    index = KnowledgeIndex(settings.knowledge_dir, settings.knowledge_db)
    index.rebuild()
    return index


def test_registry_contains_all_dba_tools(settings):
    registry = build_registry(settings, knowledge_index=_index(settings))
    names = {schema["function"]["name"] for schema in registry.schemas()}
    assert {
        "search_knowledge",
        "analyze_statistics_io",
        "analyze_statistics_time",
        "analyze_execution_plan",
        "analyze_deadlock_xml",
    } <= names


def test_file_analyzer_schemas_forbid_invented_paths(settings):
    registry = build_registry(settings, knowledge_index=_index(settings))
    schemas = {schema["function"]["name"]: schema for schema in registry.schemas()}

    for name in ("analyze_execution_plan", "analyze_deadlock_xml"):
        description = schemas[name]["function"]["description"]
        assert "usuario" in description
        assert "nunca inventes rutas" in description


def test_registry_search_executes_real_retrieval(settings):
    registry = build_registry(settings, knowledge_index=_index(settings))
    result = json.loads(
        registry.execute("search_knowledge", {"query": "cardinality", "top_k": 1})
    )
    assert result["results"][0]["topic"] == "statistics"


@pytest.mark.parametrize(
    "arguments",
    [{}, {"query": 7}, {"query": "x", "top_k": "5"}, {"query": "x", "extra": 1}],
)
def test_registry_rejects_invalid_knowledge_arguments(settings, arguments):
    registry = build_registry(settings, knowledge_index=_index(settings))
    with pytest.raises(ToolValidationError):
        registry.execute("search_knowledge", arguments)
