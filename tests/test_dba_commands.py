from app.main import HELP, _show_dba, _show_knowledge


class KnowledgeStub:
    def stats(self):
        return {"documents": 13, "categories": ["indexing", "performance"]}


def test_help_contains_dba_commands():
    assert "/dba" in HELP
    assert "/knowledge" in HELP


def test_dba_command_output(settings, capsys):
    _show_dba(settings)
    output = capsys.readouterr().out
    assert "DBA MODE" in output
    assert "SQL Server specialization enabled" in output
    assert settings.model_display_name in output


def test_knowledge_command_uses_real_stats(capsys):
    _show_knowledge(KnowledgeStub())
    output = capsys.readouterr().out
    assert "Documentos indexados: 13" in output
    assert "indexing, performance" in output
