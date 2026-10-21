const $ = (id) => document.getElementById(id);
const state = { studentId: null, speaking: false };

const REC = window.SpeechRecognition || window.webkitSpeechRecognition;
const synth = window.speechSynthesis;

function setStatus(t) { $("status").textContent = t; }
function log(kind, text) {
  const d = document.createElement("div");
  d.className = kind; d.textContent = `[${kind}] ${text}`;
  $("log").prepend(d);
}

function renderBoard(wb) {
  const board = $("board");
  if (!wb || wb.action === "clear") { board.innerHTML = ""; return; }
  let html = String(wb.content || "");
  if (wb.highlight) {
    const i = html.indexOf(wb.highlight);
    if (i >= 0) {
      html =
        html.slice(0, i) +
        "<mark>" + wb.highlight + "</mark>" +
        html.slice(i + wb.highlight.length);
    }
  }
  board.innerHTML = html;
}

function speak(text) {
  return new Promise((resolve) => {
    if (!text || !synth) return resolve();
    synth.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 1.0; u.pitch = 1.0;
    u.onend = () => { state.speaking = false; resolve(); };
    u.onerror = () => { state.speaking = false; resolve(); };
    state.speaking = true;
    synth.speak(u);
  });
}

async function callStart() {
  setStatus("starting…");
  const r = await fetch("/api/start", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ student_id: state.studentId }),
  });
  const data = await r.json();
  state.studentId = data.student_id;
  $("concept").textContent = `Concept #${data.concept_index + 1}`;
  renderBoard(data.whiteboard);
  log("tutor", data.speak);
  if (data.degraded) log("tutor", "(degraded: fallback)");
  await speak(data.speak);
  $("talkBtn").disabled = false;
  setStatus("ready");
}

async function callTurn(text) {
  setStatus("thinking…");
  const r = await fetch("/api/turn", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ student_id: state.studentId, text }),
  });
  const data = await r.json();
  $("concept").textContent = `Concept #${data.concept_index + 1}`;
  renderBoard(data.whiteboard);
  log("you", text);
  log("tutor", data.speak);
  if (data.degraded) log("tutor", "(degraded: fallback)");
  await speak(data.speak);
  setStatus("ready");
}

function setupMic() {
  if (!REC) { setStatus("no STT in this browser"); return null; }
  const rec = new REC();
  rec.lang = "en-IN";
  rec.interimResults = false;
  rec.maxAlternatives = 1;
  let finalText = "";

  rec.onresult = (e) => {
    finalText = e.results[0][0].transcript.trim();
  };
  rec.onerror = (e) => { log("you", `stt error: ${e.error}`); setStatus("ready"); };
  rec.onend = async () => {
    $("talkBtn").classList.remove("active");
    if (finalText) await callTurn(finalText);
    else setStatus("ready");
  };
  return rec;
}

const rec = setupMic();

$("startBtn").onclick = callStart;

$("talkBtn").onmousedown = () => {
  if (state.speaking || !rec) return;
  synth.cancel();
  $("talkBtn").classList.add("active");
  setStatus("listening…");
  try { rec.start(); } catch (_) { }
};
$("talkBtn").onmouseup = () => {
  if (rec) { try { rec.stop(); } catch (_) {} }
};

$("talkBtn").ontouchstart = (e) => { e.preventDefault(); $("talkBtn").onmousedown(); };
$("talkBtn").ontouchend = (e) => { e.preventDefault(); $("talkBtn").onmouseup(); };