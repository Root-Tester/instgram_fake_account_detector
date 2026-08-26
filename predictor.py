import numpy as np
import pandas as pd
import xgboost as xgb
from config import FEATURE_COLS
from validators import normalize_bool


def _safe_number(value: object) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def features_from_profile(profile_data: dict) -> pd.DataFrame:
    safe_data = {
        "followers": _safe_number(profile_data.get("followers", 0)),
        "followees": _safe_number(profile_data.get("followees", 0)),
        "mediacount": _safe_number(profile_data.get("mediacount", 0)),
        "posts_count": _safe_number(profile_data.get("posts_count", 0)),
        "stories_count": _safe_number(profile_data.get("stories_count", 0)),
        "is_private": normalize_bool(profile_data.get("is_private", False)),
        "is_verified": normalize_bool(profile_data.get("is_verified", False)),
        "profile_pic_url": str(profile_data.get("profile_pic_url", "")).strip(),
        "username": str(profile_data.get("username", "")).strip(),
        "full_name": str(profile_data.get("full_name", "")).strip(),
        "biography": str(profile_data.get("biography", "")).strip(),
        "external_url": str(profile_data.get("external_url", "")).strip(),
    }

    df = pd.DataFrame([safe_data])

    df["has_profile_pic"] = df["profile_pic_url"].ne("").astype(int)
    df["has_external_url"] = df["external_url"].ne("").astype(int)

    df["follower_followee_ratio"] = df["followers"] / (df["followees"] + 1)
    df["media_per_follower"] = df["mediacount"] / (df["followers"] + 1)
    df["followee_per_media"] = df["followees"] / (df["mediacount"] + 1)

    df["username_length"] = df["username"].str.len().fillna(0)
    df["full_name_length"] = df["full_name"].str.len().fillna(0)
    df["biography_length"] = df["biography"].str.len().fillna(0)
    df["username_digit_count"] = df["username"].str.count(r"\d").fillna(0)

    for col in ["followers", "followees", "mediacount"]:
        df[f"log_{col}"] = np.log1p(df[col])

    return df[FEATURE_COLS].fillna(0)


def predict_profile(model: xgb.Booster, profile_data: dict) -> dict:
    X = features_from_profile(profile_data)
    dmatrix = xgb.DMatrix(X)
    prob = model.predict(dmatrix)[0]

    return {
        "probability_fake": float(prob),
        "is_fake": prob > 0.5,
        "confidence": "High" if prob > 0.8 or prob < 0.2 else "Medium",
    }
