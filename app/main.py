from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .tutor import start_session, handle_turn

app = FastAPI()

class StartReq(BaseModel):
    student_id: str | None = None

class TurnReq(BaseModel):
    student_id: str
    text: str

@app.post("/api/start")
def api_start(req: StartReq):
    return start_session(req.student_id)

@app.post("/api/turn")
def api_turn(req: TurnReq):
    return handle_turn(req.student_id, req.text)

@app.get("/health")
def health():
    return {"ok": True}

app.mount("/", StaticFiles(directory="static", html=True), name="static")