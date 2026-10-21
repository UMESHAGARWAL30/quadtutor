# DESIGN.md — quadtutor

## 1. Data model

SQLite. Two tables.

```sql
CREATE TABLE student (
  student_id      TEXT PRIMARY KEY,
  created_at      TEXT NOT NULL,
  current_concept INTEGER NOT NULL DEFAULT 0,   -- 0..5
  correct_streak  INTEGER NOT NULL DEFAULT 0,
  wrong_streak    INTEGER NOT NULL DEFAULT 0,
  status          TEXT NOT NULL DEFAULT 'active' -- active | done
);

CREATE TABLE turn (
  turn_id          INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id       TEXT NOT NULL REFERENCES student(student_id),
  concept_index    INTEGER NOT NULL,
  ts               TEXT NOT NULL,
  student_text     TEXT,          -- post-STT
  extracted_answer TEXT,
  intent           TEXT,          -- answer | confused | off_topic
  is_correct       INTEGER,       -- nullable, set by verifier
  decision         TEXT,          -- advance | reteach | clarify
  tutor_speak      TEXT,
  whiteboard_json  TEXT,
  llm_model        TEXT,          -- prompt version in this build
  latency_ms       INTEGER,
  degraded         INTEGER NOT NULL DEFAULT 0
);
```

Choices:

- `turn` is **append-only**. The full history is reconstructable and every
  progression decision is auditable.
- Streaks live on `student` so the loop reads one row instead of scanning
  history.
- `degraded` marks turns where the LLM failed and a fallback was used, so
  evals and metrics can exclude them.
- `llm_model` currently records the prompt version (`PROMPT_VERSION`); when a
  model is also tracked it becomes a second column.
- No auth: `student_id` is minted server-side on first session. Swapping to
  real auth later only touches `student`.

## 2. Iterability

A student halfway through session 3 has a `student.current_concept` and a
`turn` history. Prompt/model changes are safe because progression is
code-owned and depends only on `concept_index` and verifier output, not on
prompt wording.

- **Rollout:** version the prompt set (`curriculum.PROMPT_VERSION`), record
  it per turn, and run `evals/run.py` against the new version before flipping
  the default. Scenarios that are sensitive to the change are added first.
- **Rollback:** flip the constant back. No migration needed because `turn`
  is append-only and old rows keep their version.
- **Curriculum structure change** (reordering the six concepts) is the one
  breaking case. Today the student stores an index; the correct fix is to
  store the concept *slug* instead, so reordering does not teleport a
  student. If a concept is removed, the student is dropped to the nearest
  surviving slug and the next turn re-teaches.
- **Model change:** swap `OPENROUTER_MODEL`, run evals, compare pass rate and
  `degraded` rate, then promote. Rollback is an env change plus restart.

## 3. Observability

Per turn, log one JSON line with:

`student_id, turn_id, concept_index, prompt_version, llm_model,
stt_latency_ms, llm_latency_ms, tts_latency_ms, intent, is_correct,
decision, degraded, llm_parse_ok, tokens_in, tokens_out, reason`.

Alerts:

- `degraded` rate > 2% over 10 minutes.
- `llm_parse_ok == false` rate > 1%.
- p95 `llm_latency_ms` > 6000 ms.
- **Re-teach loop signal:** same student gets `decision == reteach` three
  turns in a row on the same concept. Means the re-teach is not working.

Finding "the tutor got worse" before a student tells you:

- The eval suite runs on a schedule against the live default prompt+model.
  A drop in scenario pass rate pages.
- Intent distribution shift (e.g. `confused` share jumping week over week) is
  an early smell that explanations regressed.

## 4. Latency

Per-turn budget:

- STT: ~300–800 ms (browser-dependent).
- LLM: ~1.5–4 s (dominant term).
- TTS first-audio: ~200–500 ms.

What the user *perceives* is the gap between finishing speaking and the
tutor starting to talk.

Mitigations, in order of value:

1. Speak a short ack ("mm-hm, let me check") immediately after STT so silence
   never exceeds ~400 ms.
2. Stream the LLM's `speak` field and start TTS on the first sentence rather
   than waiting for the full JSON. (Not implemented in this build; noted in
   "what's ugly".)
3. Cap `max_tokens` on the extraction call and keep extraction and phrasing
   as separate, cheaper calls.
4. Pre-render the whiteboard from code while TTS is playing, so draw is free.

Do **not** optimise STT — it is not the dominant term and browser quality is
fine per the brief.

## 5. Metrics

North star: **concepts mastered per session** (a concept is mastered when the
code-owned rule advances past it).

Supporting:

- Median turns-to-advance per concept (lower is better; a floor guards
  against the tutor rubber-stamping).
- `reteach` rate per concept — high on a specific concept means a bad
  explanation, not a bad student.
- Session completion: fraction of six concepts reached.
- `degraded` rate: product health, not student learning.

The number I would look at first: **turns-to-advance for concept 3
(factorisation)**. It is the concept most likely to expose a bad re-teach and
the earliest place the loop's quality shows up.

## 6. What's ugly

- Whiteboard is a styled `div`; no math typesetting, no step history layout.
  Two days: KaTeX render + scrollable step list.
- No auth; `student_id` is server-minted but lives in browser memory. Two
  days: anonymous-session cookie with server-side mint.
- Extraction and phrasing are two LLM calls with no shared context beyond the
  turn. A smarter single call with tool-style output would cut latency ~40%.
- Evals assert on `decision` and `concept_index` only; they do not judge
  explanation quality. Two days: a small LLM-as-judge rubric on re-teach
  turns, gated behind a flag so it never blocks the deterministic evals.
- Sims are best-effort and not part of CI; they are a manual sanity tool.
- Highlight is applied by string match; if the LLM gives a highlight not
  present in `content`, nothing is marked. Two days: have the LLM return
  `(content, highlight_start, highlight_end)` instead.