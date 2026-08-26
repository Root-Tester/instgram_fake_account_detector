import json
from pathlib import Path
from typing import Any

from advanced_analysis import ReverseImageSearchProvider, analyze_profiles
from model_loader import load_model


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

    def predict_profile(
        self,
        profile: dict[str, Any],
        reverse_image_provider: ReverseImageSearchProvider | None = None,
    ) -> dict[str, Any]:
        return analyze_profiles(self.model, [profile], reverse_image_provider)[0]

    def predict_batch(
        self,
        profiles: list[dict[str, Any]],
        reverse_image_provider: ReverseImageSearchProvider | None = None,
    ) -> list[dict[str, Any]]:
        return analyze_profiles(self.model, profiles, reverse_image_provider)

    def predict_file(self, file_path: str | Path) -> list[dict[str, Any]]:
        with Path(file_path).open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if isinstance(payload, dict):
            return [self.predict_profile(payload)]

        if isinstance(payload, list):
            return self.predict_batch(payload)

        raise ValueError("JSON file must contain a profile object or a list of profile objects.")

    def predict_text(self, json_text: str) -> list[dict[str, Any]]:
        payload = json.loads(json_text)
        if isinstance(payload, dict):
            return [self.predict_profile(payload)]
        if isinstance(payload, list):
            return self.predict_batch(payload)
        raise ValueError("JSON text must contain a profile object or a list of profile objects.")


__all__ = ["FakeProfileDetectorSDK"]
