import json, sys
from pathlib import Path
from unittest.mock import patch

from app import tutor as tutor_mod
from app.state import decide, apply
from app.curriculum import CONCEPTS
from app.schemas import TutorTurn
from app.llm import LLMResult

HERE = Path(__file__).resolve().parent
SCENARIOS = json.loads((HERE / "scenarios.json").read_text())

def run_one(sc):
    fake_turn = TutorTurn(**sc["fake_llm"])
    fake_res = LLMResult(True, data=sc["fake_llm"], raw=json.dumps(sc["fake_llm"]), latency_ms=10)
    student = dict(sc["student_before"], student_id="eval-student")

    with patch.object(tutor_mod, "call_llm", return_value=fake_res), \
         patch.object(tutor_mod, "get_or_create_student", return_value=student), \
         patch.object(tutor_mod, "update_student", lambda s: None), \
         patch.object(tutor_mod, "record_turn", lambda **kw: None):
        result = tutor_mod.handle_turn("eval-student", sc["student_text"])

    expect = sc["expect"]
    actual = {
        "decision": result["decision"],
        "concept_index": result["concept_index"],
    }
    if "status" in expect:
        # recompute status through the same apply() so we can assert on it
        new_s = apply(student, result["decision"], fake_turn.is_correct, len(CONCEPTS))
        actual["status"] = new_s["status"]

    diffs = {k: (v, actual.get(k)) for k, v in expect.items() if actual.get(k) != v}
    return diffs

def main():
    failures = 0
    for sc in SCENARIOS:
        diffs = run_one(sc)
        if diffs:
            failures += 1
            print(f"FAIL  {sc['id']}")
            for k, (want, got) in diffs.items():
                print(f"      {k}: want {want!r}, got {got!r}")
        else:
            print(f"ok    {sc['id']}")
    print(f"\n{len(SCENARIOS) - failures}/{len(SCENARIOS)} passed")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()