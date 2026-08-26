#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"

if [[ -f .env ]]; then
	set -a
	. ./.env
	set +a
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
if [[ -x .venv/bin/python && -z "${PYTHON_BIN_OVERRIDE:-}" ]]; then
	PYTHON_BIN=".venv/bin/python"
fi

exec "$PYTHON_BIN" -m streamlit run src/instgram_fake_account_detector/streamlit_app.py \
	--server.headless "${STREAMLIT_HEADLESS:-true}" \
	--server.address "${HOST:-0.0.0.0}" \
	--server.port "${PORT:-8501}"
