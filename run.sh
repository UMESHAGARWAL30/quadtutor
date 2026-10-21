#!/usr/bin/env bash
set -euo pipefail
[ -f .env ] || cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
