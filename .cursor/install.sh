#!/usr/bin/env bash
#
# TradeMind Cloud Agent bootstrap (idempotent).
#
# Prepares two isolated virtualenvs, both gitignored:
#   * master/api/.venv       -> Master API (FastAPI + pydantic v2) + research deps (numpy/pandas)
#   * indicator-worker/.venv -> Indicator Worker (FastAPI 0.83 + pydantic v1)
#
# The worker's committed requirements.txt pins numpy/pandas builds that predate
# CPython 3.12 wheels (they target the Python 3.8 Docker image). For local dev on
# the Cloud Agent's Python 3.12 we install version-compatible builds that keep the
# same pydantic v1 / FastAPI 0.83 API surface the worker code relies on.
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

# --- System dependencies (only if missing) ---------------------------------
if ! python3 -m venv --help >/dev/null 2>&1; then
  echo "[install] installing python3-venv/pip/dev via apt"
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3-venv python3-pip python3-dev
fi

# --- Master API venv (+ research: numpy/pandas) ----------------------------
echo "[install] setting up master/api/.venv"
python3 -m venv master/api/.venv
master/api/.venv/bin/python -m pip install --upgrade pip -q
master/api/.venv/bin/python -m pip install -q -r master/api/requirements.txt
master/api/.venv/bin/python -m pip install -q "numpy>=1.26,<2" "pandas>=2.1,<2.3"

# --- Indicator Worker venv (pydantic v1, 3.12-compatible builds) -----------
echo "[install] setting up indicator-worker/.venv"
python3 -m venv indicator-worker/.venv
indicator-worker/.venv/bin/python -m pip install --upgrade pip -q
indicator-worker/.venv/bin/python -m pip install -q \
  "pydantic==1.10.13" \
  "fastapi==0.83.0" \
  "uvicorn[standard]==0.18.3" \
  "numpy>=1.26,<2" \
  "pandas>=2.1,<2.3" \
  "prometheus-fastapi-instrumentator==5.11.2" \
  "pyyaml==6.0.1" \
  "requests==2.31.0" \
  "httpx==0.24.1"

echo "[install] done"
