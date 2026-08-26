"""Train the supervised post-content model.

Input JSON may be a list of objects or a mapping of IDs to objects. Each row
must contain ``text`` (or ``caption``) and ``label``/``is_fake``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

from post_model import build_post_model, normalize_post_label, save_post_model
from instgram_fake_account_detector.config import POST_DATA_PATH, POST_MODEL_PATH
from instgram_fake_account_detector.post_model import build_post_model, normalize_post_label, save_post_model


def load_rows(path: str | Path) -> tuple[list[str], list[int]]:
    source = Path(path)
    if source.suffix.lower() == ".jsonl":
        raw: Any = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    else:
        raw = json.loads(source.read_text(encoding="utf-8"))
    rows = list(raw.values()) if isinstance(raw, dict) else raw
    if not isinstance(rows, list) or not rows:
        raise ValueError("Training data must be a non-empty JSON list, mapping, or JSONL file.")

    texts: list[str] = []
    labels: list[int] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Row {index} must be an object.")
        text = str(row.get("text", row.get("caption", ""))).strip()
        if not text:
            raise ValueError(f"Row {index} is missing text/caption.")
        label_value = row.get("label", row.get("is_fake"))
        if label_value is None:
            raise ValueError(f"Row {index} is missing label/is_fake.")
        texts.append(text)
        labels.append(normalize_post_label(label_value))
    if len(set(labels)) < 2:
        raise ValueError("Training data must contain both real and fake labels.")
    return texts, labels


def train(input_path: str | Path, output_path: str | Path) -> None:
    texts, labels = load_rows(input_path)
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    model = build_post_model()
    model.fit(train_texts, train_labels)
    predictions = model.predict(test_texts)
    probabilities = model.predict_proba(test_texts)[:, 1]
    print(f"Rows: {len(texts)}")
    print(f"Accuracy: {accuracy_score(test_labels, predictions):.3f}")
    print(f"ROC AUC: {roc_auc_score(test_labels, probabilities):.3f}")
    print(classification_report(test_labels, predictions, target_names=["real", "fake"], zero_division=0))
    save_post_model(model, output_path)
    print(f"Saved supervised post model to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a supervised fake-post text classifier.")
    parser.add_argument("input", nargs="?", default=str(POST_DATA_PATH), help="Labeled .json, .jsonl, or JSON mapping")
    parser.add_argument("--output", default=str(POST_MODEL_PATH))
    arguments = parser.parse_args()
    train(arguments.input, arguments.output)
