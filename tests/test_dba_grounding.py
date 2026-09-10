from app.config import PROJECT_ROOT
from evals.run_dba_eval import select_questions


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8").casefold()


def test_statistics_io_guidance_requires_plan_evidence_for_operators():
    prompt = _read("app/prompts/dba_system.md")
    knowledge = _read("knowledge/sql-server/performance/evidence-first-tuning.md")

    for operator in ("table scan", "index scan", "index seek", "key lookup"):
        assert operator in prompt
        assert operator in knowledge
    assert "`scan count` no identifica el operador físico" in prompt
    assert "only execution-plan evidence can identify those operators" in knowledge


def test_actual_and_estimated_plan_capture_guidance_is_explicit():
    prompt = _read("app/prompts/dba_system.md")
    knowledge = _read("knowledge/sql-server/performance/evidence-first-tuning.md")

    for text in (prompt, knowledge):
        assert "showplan_xml" in text
        assert "statistics xml" in text
        assert "statistics profile" in text
        assert "ctrl+m" in text
    assert "plan estimado sin ejecutar la consulta" in prompt
    assert "must never be presented as ways to capture an actual plan" in knowledge


def test_artifact_gate_rules_remain_in_dba_prompt():
    prompt = _read("app/prompts/dba_system.md")

    assert "ruta relativa de un archivo existente" in prompt
    assert "nunca inventes una ruta" in prompt


def test_targeted_evaluation_selects_requested_cases_in_source_order():
    questions = [{"id": "first"}, {"id": "second"}, {"id": "third"}]

    selected = select_questions(questions, ["third", "first"])

    assert [question["id"] for question in selected] == ["first", "third"]


def test_targeted_evaluation_rejects_unknown_case():
    questions = [{"id": "known"}]

    try:
        select_questions(questions, ["missing"])
    except ValueError as exc:
        assert str(exc) == "IDs de evaluación desconocidos: missing"
    else:
        raise AssertionError("Se esperaba ValueError para un ID desconocido")
