#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
exec python -m streamlit run app.py \
	--server.headless true \
	--server.address "${HOST:-0.0.0.0}" \
	--server.port "${PORT:-8501}"
