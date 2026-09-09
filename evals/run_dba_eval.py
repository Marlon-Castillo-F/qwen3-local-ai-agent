from __future__ import annotations

import argparse
import json
import tempfile
import time
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.agent import Agent
from app.client import LlamaClient
from app.config import PROJECT_ROOT, Settings
from app.memory import MemoryStore
from app.tools import build_registry


def _contains_any(text: str, terms: list[str]) -> bool:
    folded = text.casefold()
    return any(term.casefold() in folded for term in terms)


def evaluate_answer(answer: str, question: dict[str, Any]) -> dict[str, Any]:
    concept_groups = question.get("required_concepts", [])
    concepts = [_contains_any(answer, group) for group in concept_groups]
    forbidden = [
        claim
        for claim in question.get("forbidden_claims", [])
        if claim.casefold() in answer.casefold()
    ]
    return {
        "concept_groups_met": sum(concepts),
        "concept_groups_total": len(concepts),
        "missing_concept_groups": [
            concept_groups[index]
            for index, matched in enumerate(concepts)
            if not matched
        ],
        "forbidden_claim_hits": forbidden,
        "deterministic_status": (
            "pass" if concepts and all(concepts) and not forbidden else "needs_review"
        ),
        "human_review_required": True,
    }


def select_questions(
    questions: list[dict[str, Any]], question_ids: list[str] | None
) -> list[dict[str, Any]]:
    if not question_ids:
        return questions
    requested = set(question_ids)
    available = {question["id"] for question in questions}
    unknown = sorted(requested - available)
    if unknown:
        raise ValueError(f"IDs de evaluación desconocidos: {', '.join(unknown)}")
    return [question for question in questions if question["id"] in requested]


def run_evaluation(
    questions_path: Path,
    output_path: Path,
    label: str,
    question_ids: list[str] | None = None,
) -> dict[str, Any]:
    definition = json.loads(questions_path.read_text(encoding="utf-8"))
    questions = select_questions(definition["questions"], question_ids)
    base_settings = Settings()
    started = time.monotonic()
    results: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="dba-eval-") as temporary:
        temporary_root = Path(temporary)
        settings = replace(
            base_settings,
            workspace=temporary_root / "workspace",
            reports_dir=temporary_root / "reports",
            logs_dir=temporary_root / "logs",
            data_dir=temporary_root / "data",
            memory_db=temporary_root / "data" / "memory.db",
            knowledge_db=temporary_root / "data" / "knowledge.db",
        )
        settings.ensure_directories()
        registry = build_registry(settings)
        client = LlamaClient(settings)
        for index, question in enumerate(questions, start=1):
            memory = MemoryStore(temporary_root / f"question-{index}.db")
            agent = Agent(client, registry, memory, settings)
            events: list[tuple[str, str]] = []
            question_started = time.monotonic()
            error = None
            answer = ""
            try:
                answer = agent.run(
                    question["question"],
                    lambda kind, value: events.append((kind, value)),
                )
            except Exception as exc:  # The evaluation must preserve model failures.
                error = f"{type(exc).__name__}: {exc}"
            finally:
                memory.close()
            results.append(
                {
                    "id": question["id"],
                    "question": question["question"],
                    "answer": answer,
                    "duration_seconds": round(time.monotonic() - question_started, 3),
                    "tool_calls": [value for kind, value in events if kind == "tool_call"],
                    "tool_results": [
                        value for kind, value in events if kind == "tool_result"
                    ],
                    "error": error,
                    "evaluation": evaluate_answer(answer, question),
                }
            )
            print(f"[{index}/{len(questions)}] {question['id']}", flush=True)

    tool_counts = Counter(
        tool
        for result in results
        for tool in result["tool_calls"]
    )
    summary = {
        "questions": len(results),
        "completed_answers": sum(not result["error"] for result in results),
        "errors": sum(bool(result["error"]) for result in results),
        "deterministic_passes": sum(
            result["evaluation"]["deterministic_status"] == "pass"
            for result in results
        ),
        "forbidden_claim_hits": sum(
            len(result["evaluation"]["forbidden_claim_hits"])
            for result in results
        ),
        "concept_groups_met": sum(
            result["evaluation"]["concept_groups_met"] for result in results
        ),
        "concept_groups_total": sum(
            result["evaluation"]["concept_groups_total"] for result in results
        ),
        "tool_calls": dict(sorted(tool_counts.items())),
        "human_review_required": True,
    }
    payload = {
        "schema_version": 1,
        "label": label,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": settings.model_display_name,
        "engine": settings.engine,
        "duration_seconds": round(time.monotonic() - started, 3),
        "questions_file": str(questions_path.relative_to(PROJECT_ROOT)),
        "summary": summary,
        "results": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecuta la evaluación DBA reproducible")
    parser.add_argument(
        "--questions",
        type=Path,
        default=PROJECT_ROOT / "evals" / "dba_questions.json",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument(
        "--question-id",
        action="append",
        dest="question_ids",
        help="Ejecuta solo este ID; puede repetirse y conserva el orden del archivo.",
    )
    args = parser.parse_args()
    payload = run_evaluation(
        args.questions,
        args.output,
        args.label,
        question_ids=args.question_ids,
    )
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
