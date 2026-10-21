ADVANCE_AFTER = 2
RETEACH_AFTER = 2

def decide(student_row: dict, is_correct, intent: str) -> str:
    """Return 'advance' | 'reteach' | 'clarify'. Overrides the LLM's suggestion."""
    if intent == "off_topic":
        return "clarify"
    if is_correct is True:
        return "advance" if student_row["correct_streak"] + 1 >= ADVANCE_AFTER else "clarify"
    if is_correct is False:
        return "reteach" if student_row["wrong_streak"] + 1 >= RETEACH_AFTER else "clarify"
    return "clarify"

def apply(student_row: dict, decision: str, is_correct, num_concepts: int) -> dict:
    s = dict(student_row)
    if is_correct is True:
        s["correct_streak"] += 1
        s["wrong_streak"] = 0
    elif is_correct is False:
        s["wrong_streak"] += 1
        s["correct_streak"] = 0

    if decision == "advance" and s["correct_streak"] >= ADVANCE_AFTER:
        if s["current_concept"] >= num_concepts - 1:
            s["status"] = "done"
        else:
            s["current_concept"] += 1
        s["correct_streak"] = 0
        s["wrong_streak"] = 0
    return s