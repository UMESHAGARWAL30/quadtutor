# app/logging_utils.py
import json
import logging
import sys
import time
from contextlib import contextmanager

logger = logging.getLogger("quadtutor")
if not logger.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)


def log_turn(**fields):
    """Emit one JSON line per turn. Fields match DESIGN.md observability."""
    payload = {"event": "turn", **fields}
    logger.info(json.dumps(payload, default=str))


@contextmanager
def timer():
    """Usage:  with timer() as t: ...   ->  t['ms'] after exit."""
    t = {"ms": 0}
    start = time.time()
    try:
        yield t
    finally:
        t["ms"] = int((time.time() - start) * 1000)