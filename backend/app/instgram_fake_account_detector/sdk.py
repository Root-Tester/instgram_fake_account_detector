import json
from pathlib import Path
from typing import Any

import requests
from instgram_fake_account_detector.advanced_analysis import (
    ReverseImageSearchProvider,
    analyze_profiles,
)
from instgram_fake_account_detector.model_loader import load_model


class FakeProfileDetectorSDK:
    """Python SDK for local inference or a deployed FastAPI backend."""

    def __init__(
        self,
        model_path: str | None = None,
        api_base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        if model_path and api_base_url:
            raise ValueError("Choose either model_path or api_base_url, not both.")
        self.model_path = Path(model_path) if model_path else None
        self.api_base_url = api_base_url.rstrip("/") if api_base_url else None
        self.timeout = timeout
        self.model = None
        if self.api_base_url is None:
            self.model = (
                load_model()
                if self.model_path is None
                else self._load_model_from_path(self.model_path)
            )

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
        if self.api_base_url:
            return self._post("/api/v1/profiles/analyze", {"profile": profile})
        if self.model is None:
            raise RuntimeError("The local detector model is not loaded.")
        return analyze_profiles(self.model, [profile], reverse_image_provider)[0]

    def predict_batch(
        self,
        profiles: list[dict[str, Any]],
        reverse_image_provider: ReverseImageSearchProvider | None = None,
    ) -> list[dict[str, Any]]:
        if self.api_base_url:
            response = self._post(
                "/api/v1/profiles/batch", {"profiles": profiles}
            )
            return response["results"]
        if self.model is None:
            raise RuntimeError("The local detector model is not loaded.")
        return analyze_profiles(self.model, profiles, reverse_image_provider)

    def analyze_post(self, post_url: str) -> dict[str, Any]:
        """Analyze a public post through the deployed API."""
        if not self.api_base_url:
            raise ValueError("analyze_post requires api_base_url.")
        return self._post("/api/v1/posts/analyze", {"post_url": post_url})

    def health(self) -> dict[str, Any]:
        """Check the configured remote API."""
        if not self.api_base_url:
            return {"status": "ok", "service": "local"}
        response = requests.get(
            f"{self.api_base_url}/health", timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            f"{self.api_base_url}{path}",
            json=payload,
            timeout=self.timeout,
        )
        try:
            body = response.json()
        except ValueError as exc:
            raise RuntimeError(
                f"API returned a non-JSON response ({response.status_code})."
            ) from exc
        if not response.ok:
            detail = body.get("detail", f"Request failed ({response.status_code})")
            raise RuntimeError(str(detail))
        return body

    def predict_file(self, file_path: str | Path) -> list[dict[str, Any]]:
        with Path(file_path).open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if isinstance(payload, dict):
            return [self.predict_profile(payload)]

        if isinstance(payload, list):
            return self.predict_batch(payload)

        raise ValueError(
            "JSON file must contain a profile object or a list of profile objects."
        )

    def predict_text(self, json_text: str) -> list[dict[str, Any]]:
        payload = json.loads(json_text)
        if isinstance(payload, dict):
            return [self.predict_profile(payload)]
        if isinstance(payload, list):
            return self.predict_batch(payload)
        raise ValueError(
            "JSON text must contain a profile object or a list of profile objects."
        )


__all__ = ["FakeProfileDetectorSDK"]
