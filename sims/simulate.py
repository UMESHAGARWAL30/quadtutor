import json
from unittest.mock import patch
from app import tutor as tutor_mod
from app.state import decide, apply
from app.curriculum import CONCEPTS
from app.llm import LLMResult

SCRIPT = [
    {"student_text": "x is 1", "fake_llm": {"extracted_answer":"1","intent":"answer","is_correct":False,"decision":"clarify","reason":"wrong","speak":"Not quite.","whiteboard":{"action":"add","content":"1 - 5 + 6 = 2 ≠ 0","highlight":"2 ≠ 0"}}},
    {"student_text": "I don't understand", "fake_llm": {"extracted_answer":None,"intent":"confused","is_correct":False,"decision":"reteach","reason":"confused","speak":"Let me try again.","whiteboard":{"action":"replace","content":"x^2 - 5x + 6 = (x-2)(x-3)","highlight":"(x-2)"}}},
    {"student_text": "so x can be 2?", "fake_llm": {"extracted_answer":"2","intent":"answer","is_correct":True,"decision":"clarify","reason":"correct","speak":"Yes.","whiteboard":{"action":"add","content":"x=2 ✓","highlight":"x=2"}}},
    {"student_text": "and 3 also works", "fake_llm": {"extracted_answer":"3","intent":"answer","is_correct":True,"decision":"clarify","reason":"correct","speak":"Right, 2 and 3.","whiteboard":{"action":"add","content":"x=3 ✓","highlight":"x=3"}}},
]

def main():
    student = {"student_id": "sim-1", "current_concept": 0,
               "correct_streak": 0, "wrong_streak": 0, "status": "active"}
    print(f"start concept={student['current_concept']}")
    for i, step in enumerate(SCRIPT, 1):
        fake = LLMResult(True, data=step["fake_llm"], raw=json.dumps(step["fake_llm"]), latency_ms=5)
        with patch.object(tutor_mod, "call_llm", return_value=fake), \
             patch.object(tutor_mod, "get_or_create_student", return_value=student), \
             patch.object(tutor_mod, "update_student", lambda s: None), \
             patch.object(tutor_mod, "record_turn", lambda **kw: None):
            r = tutor_mod.handle_turn(student["student_id"], step["student_text"])
        d = decide(student, step["fake_llm"]["is_correct"], step["fake_llm"]["intent"])
        student = apply(student, d, step["fake_llm"]["is_correct"], len(CONCEPTS))
        print(f"turn {i}: said={step['student_text']!r} "
              f"correct={step['fake_llm']['is_correct']} decision={d} "
              f"-> concept={student['current_concept']} status={student['status']}")

if __name__ == "__main__":
    main()