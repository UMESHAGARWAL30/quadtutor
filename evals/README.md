# evals

Regression scenarios for the tutor loop.

## Run

```bash
python evals/run.py
```

Exit code 0 on all-pass, 1 on any failure. Offline — uses a fake LLM, so no
API key or network is needed.

## What is tested

Each scenario pins a *fake* LLM response (extracted answer, intent,
correctness) and a *starting* student state, then asserts on the code-owned
outcome: `decision`, resulting `concept_index`, and (where relevant)
`status`.

Two scenarios specifically prove the LLM's own `decision` field is ignored:

- `advance_requires_streak_not_single_correct`
- `concept_progression_independent_of_llm_decision`

## Adding a scenario

Append to `scenarios.json`:

```json
{
  "id": "unique_snake_case",
  "student_text": "what the student says",
  "fake_llm": { "...TutorTurn fields..." : "..." },
  "student_before": { "correct_streak": 0, "wrong_streak": 0,
                      "current_concept": 0, "status": "active" },
  "expect": { "decision": "advance", "concept_index": 1 }
}
```

Prefer a few scenarios that each pin a distinct behaviour over many shallow
ones.

## What is *not* tested here

- Explanation quality of the tutor (see DESIGN.md "what's ugly").
- Real LLM latency or failure modes (drill them manually with the fallback
  path in `app/tutor.py`).