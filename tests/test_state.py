# tests/test_state.py
from app.state import decide, apply

def test_two_correct_advances():
    row = {"correct_streak": 1, "wrong_streak": 0, "current_concept": 0, "status": "active"}
    assert decide(row, True, "answer") == "advance"

def test_one_correct_is_clarify():
    row = {"correct_streak": 0, "wrong_streak": 0, "current_concept": 0, "status": "active"}
    assert decide(row, True, "answer") == "clarify"

def test_two_wrong_reteaches():
    row = {"correct_streak": 0, "wrong_streak": 1, "current_concept": 0, "status": "active"}
    assert decide(row, False, "answer") == "reteach"

def test_off_topic_clarifies():
    row = {"correct_streak": 0, "wrong_streak": 0, "current_concept": 0, "status": "active"}
    assert decide(row, None, "off_topic") == "clarify"

def test_apply_advances_concept():
    row = {"correct_streak": 1, "wrong_streak": 0, "current_concept": 0, "status": "active"}
    out = apply(row, "advance", True, 6)
    assert out["current_concept"] == 1
    assert out["correct_streak"] == 0

def test_apply_last_concept_marks_done():
    row = {"correct_streak": 1, "wrong_streak": 0, "current_concept": 5, "status": "active"}
    out = apply(row, "advance", True, 6)
    assert out["status"] == "done"
    assert out["current_concept"] == 5