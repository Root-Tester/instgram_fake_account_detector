import json
from pathlib import Path
from typing import Any

from instgram_fake_account_detector.config import SAMPLE_PATH


def load_json_from_text(text: str) -> Any:
    return json.loads(text)


def normalize_profiles(payload: Any) -> list[dict]:
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list) and all(isinstance(profile, dict) for profile in payload):
        if not payload:
            raise ValueError("JSON array must contain at least one profile object.")
        return payload
    raise ValueError("JSON must be a profile object or an array of profile objects.")


def load_json_file(file_obj) -> Any:
    return json.load(file_obj)


def load_sample_json() -> Any:
    if not SAMPLE_PATH.exists():
        raise FileNotFoundError(f"Sample file not found: {SAMPLE_PATH}")

    with SAMPLE_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)
