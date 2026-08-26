#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ -f .env ]]; then
	set -a
	# .env is intentionally optional for local and hosted deployment.
	. ./.env
	set +a
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
if [[ -x .venv/bin/python && -z "${PYTHON_BIN_OVERRIDE:-}" ]]; then
	PYTHON_BIN=".venv/bin/python"
fi

exec "$PYTHON_BIN" -m streamlit run app.py \
	--server.headless true \
	--server.address "${HOST:-0.0.0.0}" \
	--server.port "${PORT:-8501}"
