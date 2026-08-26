"""Compatibility entry point for existing Streamlit commands."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from instgram_fake_account_detector.streamlit_app import *  # noqa: F401,F403
