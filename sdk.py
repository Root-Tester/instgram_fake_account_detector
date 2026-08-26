import json
from pathlib import Path
from typing import Any

from model_loader import load_model
from predictor import predict_profile


class FakeProfileDetectorSDK:
    """Simple Python SDK for batch or single-profile prediction."""

    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = Path(model_path) if model_path else None
        self.model = load_model() if self.model_path is None else self._load_model_from_path(self.model_path)

    def _load_model_from_path(self, model_path: Path):
        from xgboost import Booster

        model = Booster()
        model.load_model(str(model_path))
        return model

    def predict_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        return predict_profile(self.model, profile)

    def predict_batch(self, profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [predict_profile(self.model, profile) for profile in profiles]

    def predict_file(self, file_path: str | Path) -> list[dict[str, Any]]:
        with Path(file_path).open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if isinstance(payload, dict):
            return [predict_profile(self.model, payload)]

        if isinstance(payload, list):
            return [predict_profile(self.model, item) for item in payload]

        raise ValueError("JSON file must contain a profile object or a list of profile objects.")

    def predict_text(self, json_text: str) -> list[dict[str, Any]]:
        payload = json.loads(json_text)
        if isinstance(payload, dict):
            return [predict_profile(self.model, payload)]
        if isinstance(payload, list):
            return [predict_profile(self.model, item) for item in payload]
        raise ValueError("JSON text must contain a profile object or a list of profile objects.")


__all__ = ["FakeProfileDetectorSDK"]
