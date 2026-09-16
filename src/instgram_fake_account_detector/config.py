import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parents[1]
DATA_DIR = PROJECT_DIR / "data"
MODEL_DIR = PROJECT_DIR / "models"
MODEL_PATH = Path(
    os.getenv("PROFILE_MODEL_PATH") or MODEL_DIR / "fake_profile_model.model"
)
POST_MODEL_PATH = MODEL_DIR / "post_content_model.joblib"
SAMPLE_PATH = PROJECT_DIR / "examples" / "sample.json"
PROFILE_DATA_PATH = DATA_DIR / "profiles" / "fake_profile_model.json"
POST_DATA_PATH = DATA_DIR / "posts" / "post_training_dataset.jsonl"


def cors_origins() -> list[str]:
    """Return explicitly configured browser origins, with safe local defaults."""
    configured = os.getenv("CORS_ORIGINS", os.getenv("FRONTEND_ORIGINS", ""))
    origins = [
        origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()
    ]
    return origins or ["http://localhost:5173", "http://127.0.0.1:5173"]


FEATURE_COLS = [
    "followers",
    "followees",
    "mediacount",
    "posts_count",
    "stories_count",
    "is_private",
    "is_verified",
    "has_profile_pic",
    "follower_followee_ratio",
    "media_per_follower",
    "followee_per_media",
    "username_length",
    "full_name_length",
    "biography_length",
    "has_external_url",
    "username_digit_count",
    "log_followers",
    "log_followees",
    "log_mediacount",
]
