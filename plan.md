# plan.md — quadtutor

## Goal

Build a voice AI tutor that teaches NCERT Class 10 quadratic equations over six
sub-concepts, with a verify-and-reteach loop and a whiteboard. Judged on:
working prototype, code organisation, evals, and how thoughtful the whole
thing is.

## Scope decisions (and why)

- **STT/TTS: browser Web Speech APIs.** The brief says audio quality is not
  the point; browser APIs remove an entire moving part and keep the loop fast
  to iterate on.
- **LLM: OpenRouter, one chat-completions model, structured JSON output.**
  Structured output is what lets code verify correctness and own progression.
- **State: SQLite.** One local student, keyed by a generated `student_id`.
  No auth — noted as a deliberate simplification in DESIGN.md.
- **Whiteboard: plain HTML div, text + `<mark>` highlight.** No canvas
  library; the brief says nothing fancier is needed.
- **Correctness: deterministic.** Roots are checked in code; the LLM only
  extracts the answer and phrases the response.
- **Progression: code-owned.** Streak rules in `app/state.py` decide
  advance/reteach; the LLM's own decision is logged but overridden.

## Build order (actual)

1. Repo, `.env`, FastAPI skeleton, `/health`.
2. `app/llm.py`: one call returns the JSON contract; timeout + one retry +
   structured failure result.
3. `app/schemas.py`: pydantic contract for the tutor turn.
4. `app/curriculum.py`: six concepts, teach and check prompts, prompt version.
5. `app/verifier.py`: deterministic math checks (root, discriminant).
6. `app/state.py`: streak rules + unit tests.
7. `app/store.py`: SQLite schema, student state, append-only turns.
8. `app/tutor.py`: orchestrate the loop; code decides, LLM speaks.
9. `app/main.py`: three routes, static mount.
10. `static/`: STT → POST → TTS + whiteboard render.
11. `evals/`: fixed scenarios, one-command runner, offline fake LLM.
12. Failure drills: timeout, garbage JSON, 5xx, degraded turn logging.
13. `sims/`: simulated student sessions.
14. `DESIGN.md`, deploy, invite reviewers.

## The loop (what I will prove works)

```
teach → student speaks → STT → LLM extracts answer + intent
      → code verifies correctness → code decides advance/reteach
      → LLM phrases the decision + whiteboard → TTS + render
```

The invariant: the LLM never owns progression or correctness. It owns
language (interpret, explain) only. This makes evals and observability
possible.

## Failure handling plan

- 12s timeout, one retry, then a canned fallback line; no progress change.
- JSON parse failure → logged as `degraded`, fallback line.
- 5xx / network → fallback line, `degraded=1` on the turn.
- Deterministic parts (progress, current equation) survive an LLM outage.

## Evals plan

Eight fixed scenarios, each asserting on `decision` and `concept_index`
(and `status` where relevant). Two of them specifically prove the LLM's own
`decision` field is ignored and code-owned rules win. Run:
`python evals/run.py`. Non-zero exit on any failure.

## Risks and trade-offs

- Browser STT quality varies by browser; acceptable per brief.
- LLM phrasing may still be inconsistent; mitigated by code-owned state and
  logged `reason`.
- Single-student assumption keeps schema simple; noted in DESIGN.md.
- Offline evals don't judge explanation quality; noted as a follow-up.

## Out of scope (deliberately)

Auth, multi-tenant, audio streaming, realtime APIs, fancy whiteboard,
persistent student accounts.

## Time budget (if I had more)

Two days: KaTeX whiteboard, server-minted sessions, LLM-as-judge rubric on
re-teach quality, extraction+phrasing collapsed into one call.