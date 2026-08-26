#!/usr/bin/env bash
cd "$(dirname "$0")"
pkill -f 'python -m streamlit run app.py' || true
sleep 1
python -m streamlit run app.py
