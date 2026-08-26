"""Compatibility import for the packaged SDK."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from instgram_fake_account_detector.sdk import FakeProfileDetectorSDK

__all__ = ["FakeProfileDetectorSDK"]
