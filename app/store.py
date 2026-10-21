import sqlite3, os, uuid, datetime

DB_PATH = os.getenv("DB_PATH", "data/tutor.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS student (
  student_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  current_concept INTEGER NOT NULL DEFAULT 0,
  correct_streak INTEGER NOT NULL DEFAULT 0,
  wrong_streak INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active'
);
CREATE TABLE IF NOT EXISTS turn (
  turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id TEXT NOT NULL,
  concept_index INTEGER NOT NULL,
  ts TEXT NOT NULL,
  student_text TEXT,
  extracted_answer TEXT,
  intent TEXT,
  is_correct INTEGER,
  decision TEXT,
  tutor_speak TEXT,
  whiteboard_json TEXT,
  llm_model TEXT,
  latency_ms INTEGER,
  degraded INTEGER NOT NULL DEFAULT 0
);
"""

def _conn():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    return c

def get_or_create_student(student_id: str | None) -> dict:
    with _conn() as c:
        if not student_id:
            student_id = str(uuid.uuid4())
            c.execute(
                "INSERT INTO student(student_id, created_at) VALUES (?,?)",
                (student_id, datetime.datetime.utcnow().isoformat()),
            )
            c.commit()
        row = c.execute("SELECT * FROM student WHERE student_id=?", (student_id,)).fetchone()
        return dict(row)

def update_student(s: dict):
    with _conn() as c:
        c.execute(
            "UPDATE student SET current_concept=?, correct_streak=?, wrong_streak=?, status=? WHERE student_id=?",
            (s["current_concept"], s["correct_streak"], s["wrong_streak"], s["status"], s["student_id"]),
        )
        c.commit()

def record_turn(**kw):
    with _conn() as c:
        c.execute(
            """INSERT INTO turn(student_id,concept_index,ts,student_text,extracted_answer,intent,
                                is_correct,decision,tutor_speak,whiteboard_json,llm_model,latency_ms,degraded)
               VALUES(:student_id,:concept_index,:ts,:student_text,:extracted_answer,:intent,
                      :is_correct,:decision,:tutor_speak,:whiteboard_json,:llm_model,:latency_ms,:degraded)""",
            kw,
        )
        c.commit()