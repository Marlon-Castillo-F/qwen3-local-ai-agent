from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compare(baseline: dict[str, Any], edition: dict[str, Any]) -> dict[str, Any]:
    before = {result["id"]: result for result in baseline["results"]}
    after = {result["id"]: result for result in edition["results"]}
    if list(before) != list(after):
        raise ValueError("Las evaluaciones no contienen las mismas preguntas y orden")
    changes = []
    for question_id in before:
        left = before[question_id]["evaluation"]
        right = after[question_id]["evaluation"]
        changes.append(
            {
                "id": question_id,
                "baseline_status": left["deterministic_status"],
                "dba_edition_status": right["deterministic_status"],
                "concept_groups_delta": (
                    right["concept_groups_met"] - left["concept_groups_met"]
                ),
                "forbidden_claims_delta": (
                    len(right["forbidden_claim_hits"])
                    - len(left["forbidden_claim_hits"])
                ),
                "baseline_tools": before[question_id]["tool_calls"],
                "dba_edition_tools": after[question_id]["tool_calls"],
            }
        )
    return {
        "questions_equal": True,
        "questions": len(changes),
        "baseline": baseline["summary"],
        "dba_edition": edition["summary"],
        "delta": {
            "deterministic_passes": (
                edition["summary"]["deterministic_passes"]
                - baseline["summary"]["deterministic_passes"]
            ),
            "concept_groups_met": (
                edition["summary"]["concept_groups_met"]
                - baseline["summary"]["concept_groups_met"]
            ),
            "forbidden_claim_hits": (
                edition["summary"]["forbidden_claim_hits"]
                - baseline["summary"]["forbidden_claim_hits"]
            ),
        },
        "changes": changes,
        "interpretation": "Las métricas son heurísticas determinísticas; la exactitud global requiere revisión humana.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("edition", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = compare(_load(args.baseline), _load(args.edition))
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
