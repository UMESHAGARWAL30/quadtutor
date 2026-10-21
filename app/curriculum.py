PROMPT_VERSION = "v1"

CONCEPTS = [
    {"slug": "standard_form", "title": "Standard form and recognising a quadratic"},
    {"slug": "roots_check",   "title": "What a root is; checking a root by substitution"},
    {"slug": "factorisation", "title": "Solving by factorisation"},
    {"slug": "formula",       "title": "The quadratic formula"},
    {"slug": "discriminant",  "title": "Discriminant and nature of roots"},
    {"slug": "word_problems", "title": "Word problems"},
]

SYSTEM_TUTOR = """You are a patient NCERT Class 10 maths tutor teaching quadratic equations.
You MUST reply with a single JSON object and nothing else. No markdown fences.
Schema:
{
  "extracted_answer": string|null,
  "intent": "answer"|"confused"|"off_topic",
  "is_correct": true|false|null,
  "decision": "advance"|"reteach"|"clarify",
  "reason": string,
  "speak": string,
  "whiteboard": {"action":"add"|"replace"|"clear","content":string,"highlight":string|null}
}
Rules:
- Speak to a 15-year-old, one or two short sentences.
- Whiteboard content is plain text or simple math like "x^2 - 5x + 6 = 0".
- "highlight" is the exact substring of content you are referring to, or null.
- If the student is confused, decision="reteach" and you must explain DIFFERENTLY from the last explanation.
- "reason" is a short internal note on why you chose this decision.
"""

def teach_prompt(concept_index: int) -> str:
    c = CONCEPTS[concept_index]
    return f"Teach this concept now with a small worked step on the whiteboard: {c['title']}."

def check_prompt(concept_index: int, student_text: str) -> str:
    c = CONCEPTS[concept_index]
    return (
        f"Concept: {c['title']}. "
        f'The student just said: "{student_text}". '
        "Evaluate their understanding, extract any answer they gave, and respond."
    )