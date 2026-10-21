import json, time, httpx
from .config import OPENROUTER_API_KEY, OPENROUTER_MODEL, LLM_TIMEOUT_SECONDS, OPENROUTER_URL

class LLMResult:
    def __init__(self, ok, data=None, raw=None, error=None, latency_ms=0):
        self.ok = ok; self.data = data; self.raw = raw
        self.error = error; self.latency_ms = latency_ms

def call_llm(system_prompt: str, user_prompt: str) -> LLMResult:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 600,
    }

    last_err = None
    for attempt in range(2):  # one retry
        t0 = time.time()
        try:
            r = httpx.post(OPENROUTER_URL, headers=headers, json=body,
                           timeout=LLM_TIMEOUT_SECONDS)
            latency = int((time.time() - t0) * 1000)
            if r.status_code != 200:
                last_err = f"http_{r.status_code}"
                continue
            content = r.json()["choices"][0]["message"]["content"]
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                return LLMResult(False, raw=content, error="parse_error", latency_ms=latency)
            return LLMResult(True, data=data, raw=content, latency_ms=latency)
        except httpx.TimeoutException:
            last_err = "timeout"
        except Exception as e:
            last_err = f"exception:{type(e).__name__}"

    return LLMResult(False, error=last_err or "unknown")