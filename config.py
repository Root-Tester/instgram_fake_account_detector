from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "fake_profile_model.model"
POST_MODEL_PATH = BASE_DIR / "post_content_model.joblib"
SAMPLE_PATH = BASE_DIR / "sample.json"
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
