import datetime, json
from .llm import call_llm
from .curriculum import SYSTEM_TUTOR, teach_prompt, check_prompt, CONCEPTS, PROMPT_VERSION
from .state import decide, apply
from .store import get_or_create_student, update_student, record_turn
from .schemas import TutorTurn
from .logging_utils import log_turn

FALLBACK_SPEAK = "Sorry, I lost my train of thought. Can you say that again?"
EMPTY_BOARD = {"action": "replace", "content": "", "highlight": None}

def _fallback(student_id, concept_index, student_text, latency_ms, error):
    record_turn(
        student_id=student_id, concept_index=concept_index,
        ts=datetime.datetime.utcnow().isoformat(),
        student_text=student_text, extracted_answer=None,
        intent="off_topic", is_correct=None, decision="clarify",
        tutor_speak=FALLBACK_SPEAK, whiteboard_json=json.dumps(EMPTY_BOARD),
        llm_model=PROMPT_VERSION, latency_ms=latency_ms, degraded=1,
    )
    log_turn(
        student_id=student_id,
        concept_index=concept_index,
        prompt_version=PROMPT_VERSION,
        intent="off_topic",
        is_correct=None,
        decision="clarify",
        degraded=1,
        llm_parse_ok=False,
        llm_latency_ms=latency_ms,
        reason=f"llm_error:{error}",
    )
    return {
        "student_id": student_id, "speak": FALLBACK_SPEAK,
        "whiteboard": EMPTY_BOARD, "concept_index": concept_index,
        "decision": "clarify", "reason": f"llm_error:{error}", "degraded": True,
    }

def start_session(student_id: str | None) -> dict:
    s = get_or_create_student(student_id)
    r = call_llm(SYSTEM_TUTOR, teach_prompt(s["current_concept"]))
    if not r.ok:
        return _fallback(s["student_id"], s["current_concept"], None, r.latency_ms, r.error)
    try:
        turn = TutorTurn(**r.data)
    except Exception as e:
        return _fallback(s["student_id"], s["current_concept"], None, r.latency_ms, f"schema:{e}")

    record_turn(
        student_id=s["student_id"], concept_index=s["current_concept"],
        ts=datetime.datetime.utcnow().isoformat(),
        student_text=None, extracted_answer=None,
        intent="answer", is_correct=None, decision="clarify",
        tutor_speak=turn.speak,
        whiteboard_json=json.dumps(turn.whiteboard.model_dump()),
        llm_model=PROMPT_VERSION, latency_ms=r.latency_ms, degraded=0,
    )
    log_turn(
        student_id=s["student_id"],
        concept_index=s["current_concept"],
        prompt_version=PROMPT_VERSION,
        intent="answer",
        is_correct=None,
        decision="clarify",
        degraded=0,
        llm_parse_ok=True,
        llm_latency_ms=r.latency_ms,
        reason=turn.reason,
    )
    return {
        "student_id": s["student_id"], "speak": turn.speak,
        "whiteboard": turn.whiteboard.model_dump(),
        "concept_index": s["current_concept"],
        "decision": "clarify", "reason": turn.reason, "degraded": False,
    }

def handle_turn(student_id: str, student_text: str) -> dict:
    s = get_or_create_student(student_id)
    r = call_llm(SYSTEM_TUTOR, check_prompt(s["current_concept"], student_text))

    if not r.ok:
        return _fallback(s["student_id"], s["current_concept"], student_text, r.latency_ms, r.error)
    try:
        turn = TutorTurn(**r.data)
    except Exception as e:
        return _fallback(s["student_id"], s["current_concept"], student_text, r.latency_ms, f"schema:{e}")

    decision = decide(s, turn.is_correct, turn.intent)      # <-- code owns this
    new_s = apply(s, decision, turn.is_correct, len(CONCEPTS))
    update_student(new_s)

    record_turn(
        student_id=s["student_id"], concept_index=s["current_concept"],
        ts=datetime.datetime.utcnow().isoformat(),
        student_text=student_text, extracted_answer=turn.extracted_answer,
        intent=turn.intent,
        is_correct=None if turn.is_correct is None else int(turn.is_correct),
        decision=decision, tutor_speak=turn.speak,
        whiteboard_json=json.dumps(turn.whiteboard.model_dump()),
        llm_model=PROMPT_VERSION, latency_ms=r.latency_ms, degraded=0,
    )
    log_turn(
        student_id=s["student_id"],
        concept_index=s["current_concept"],
        prompt_version=PROMPT_VERSION,
        intent=turn.intent,
        is_correct=turn.is_correct,
        decision=decision,
        degraded=0,
        llm_parse_ok=True,
        llm_latency_ms=r.latency_ms,
        reason=turn.reason,
    )

    return {
        "student_id": s["student_id"], "speak": turn.speak,
        "whiteboard": turn.whiteboard.model_dump(),
        "concept_index": new_s["current_concept"],
        "decision": decision, "reason": turn.reason, "degraded": False,
    }