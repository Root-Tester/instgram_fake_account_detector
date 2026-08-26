"""Supervised text model for labeled Instagram post content."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from config import POST_MODEL_PATH


def normalize_post_label(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)) and value in {0, 1}:
        return int(value)
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "fake", "fraud", "scam", "misleading", "suspicious"}:
        return 1
    if normalized in {"0", "false", "real", "legitimate", "safe", "genuine"}:
        return 0
    raise ValueError("Post label must be 0/1 or a supported real/fake label.")


def build_post_model() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, strip_accents="unicode", ngram_range=(1, 2), min_df=2, max_features=50000)),
        ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
    ])


def save_post_model(model: Pipeline, path: str | Path = POST_MODEL_PATH) -> None:
    joblib.dump(model, path)


def load_post_model(path: str | Path = POST_MODEL_PATH) -> Pipeline | None:
    model_path = Path(path)
    if not model_path.exists():
        return None
    model = joblib.load(model_path)
    if not hasattr(model, "predict_proba"):
        raise ValueError(f"Invalid post model artifact: {model_path}")
    return model


def predict_post_content(model: Pipeline | None, text: str) -> dict[str, Any] | None:
    if model is None or not text.strip():
        return None
    probability = float(model.predict_proba([text])[0, 1])
    return {
        "available": True,
        "fake_probability": round(probability, 4),
        "label": "fake-or-misleading" if probability >= 0.5 else "real-appearing",
        "method": "TF-IDF n-grams with supervised logistic regression trained on labeled post text.",
    }
