"""Typed FastAPI backend for profile and public-post analysis."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field

from instgram_fake_account_detector.advanced_analysis import analyze_profiles
from instgram_fake_account_detector.config import cors_origins
from instgram_fake_account_detector.model_loader import load_model
from instgram_fake_account_detector.post_analysis import (
    analyze_post,
    get_validated_media,
)


class Profile(BaseModel):
    """Instagram profile observations accepted by the detector."""

    model_config = ConfigDict(extra="allow")

    username: str = ""
    followers: float = 0
    followees: float = 0
    mediacount: float = 0
    posts_count: float = 0
    stories_count: float = 0
    is_private: bool = False
    is_verified: bool = False

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump() if hasattr(self, "model_dump") else self.dict()


class ProfileAnalysisRequest(BaseModel):
    profile: Profile


class BatchAnalysisRequest(BaseModel):
    profiles: list[Profile] = Field(min_length=1, max_length=100)


class BatchAnalysisResponse(BaseModel):
    results: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class PostAnalysisRequest(BaseModel):
    post_url: str = Field(min_length=1, max_length=2048)

    # `url` is retained for older clients; new clients should send `post_url`.
    @classmethod
    def model_validate(
        cls, obj: Any, *args: Any, **kwargs: Any
    ) -> "PostAnalysisRequest":
        if isinstance(obj, dict) and "post_url" not in obj and "url" in obj:
            obj = {**obj, "post_url": obj["url"]}
        return super().model_validate(obj, *args, **kwargs)


class HealthResponse(BaseModel):
    status: str
    service: str


app = FastAPI(title="Instagram Fake Account Detector API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="fake-account-detector")


@app.post("/api/v1/profiles/analyze", response_model=dict[str, Any])
def analyze_profile(request: ProfileAnalysisRequest) -> dict[str, Any]:
    try:
        return analyze_profiles(load_model(), [request.profile.as_dict()])[0]
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/profiles/batch", response_model=BatchAnalysisResponse)
def analyze_batch(request: BatchAnalysisRequest) -> BatchAnalysisResponse:
    try:
        results = analyze_profiles(
            load_model(), [profile.as_dict() for profile in request.profiles]
        )
        return BatchAnalysisResponse(results=results, count=len(results))
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/posts/analyze", response_model=dict[str, Any])
def analyze_public_post(request: PostAnalysisRequest) -> dict[str, Any]:
    try:
        return analyze_post(request.post_url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/v1/media/{token}")
def validated_media(token: str) -> Response:
    media = get_validated_media(token)
    if media is None:
        raise HTTPException(
            status_code=404, detail="Validated media not found or expired."
        )
    media_type, content = media
    return Response(
        content=content,
        media_type=media_type,
        headers={"Cache-Control": "private, max-age=300"},
    )


__all__ = [
    "app",
    "Profile",
    "ProfileAnalysisRequest",
    "BatchAnalysisRequest",
    "BatchAnalysisResponse",
    "PostAnalysisRequest",
]
