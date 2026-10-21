# quadtutor

A voice AI tutor that teaches NCERT Class 10 quadratic equations across six
sub-concepts, with a verify-and-reteach loop and a whiteboard.

## What it does

- Student speaks; the tutor speaks back (browser Web Speech STT + TTS).
- A whiteboard shows text/equations and highlights the term being discussed.
- Six sub-concepts, each with a teach → check → advance/reteach loop.
- Progression is code-owned (deterministic), not decided by the LLM.
- Degrades gracefully when the LLM times out, returns garbage, or is down.

## Run locally

```bash
cp .env.example .env      # put your OpenRouter key in OPENROUTER_API_KEY
./run.sh                  # or: .\run.ps1 on Windows
# open http://localhost:8000
```

Windows (PowerShell):

```powershell
Copy-Item .env.example .env
notepad .env              # add OPENROUTER_API_KEY
.\run.ps1
```

## Tests and evals

```bash
python -m pytest tests/ -q     # unit tests (state machine, verifier)
python evals/run.py            # regression scenarios (offline, fake LLM)
python sims/simulate.py        # simulated session sanity check
```

`evals/run.py` is the regression suite: it uses a fake LLM and asserts on
code-owned decisions, so it catches prompt/model changes that would make the
tutor worse. Exit code is non-zero on any failure.

## Architecture (short)

```
mic → browser STT → POST /api/turn → LLM (JSON) → code verifies + decides
                                         ↓
              browser TTS + whiteboard ← response
```

The LLM extracts the student's answer, classifies intent, and writes the
spoken explanation and whiteboard content. The **decision** to advance or
re-teach is made by `app/state.py`, using deterministic streak rules. The
LLM's own `decision` field is logged but ignored.

## Project layout

```
app/        backend (FastAPI, LLM client, tutor loop, state, store)
static/     voice UI + whiteboard (browser STT/TTS)
evals/      regression scenarios + runner
sims/       simulated student sessions
tests/      unit tests
plan.md     hand-written build plan
DESIGN.md   design write-up (data model, iterability, observability, ...)
```

## Notes

- STT/TTS use browser APIs; audio quality is not the goal.
- A single-student model is assumed (no auth); a `student_id` is minted on
  first session. See `DESIGN.md` for the trade-off.
- No realtime/live audio APIs are used — the pipeline is `STT → LLM → TTS`.