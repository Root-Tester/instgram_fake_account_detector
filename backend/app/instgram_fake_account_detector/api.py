"""Typed FastAPI backend for profile and public-post analysis."""

from __future__ import annotations

import logging
import secrets
import threading
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.base import BaseHTTPMiddleware

from instgram_fake_account_detector.advanced_analysis import analyze_profiles
from instgram_fake_account_detector.config import (
    api_key_required,
    api_keys,
    cors_origins,
    FRONTEND_DIST,
    max_request_bytes,
)
from instgram_fake_account_detector.config import rate_limit as configured_rate_limit
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


LOGGER = logging.getLogger("instgram_fake_account_detector.api")
_rate_lock = threading.Lock()
_rate_windows: dict[str, list[float]] = {}


class ProductionBoundaryMiddleware(BaseHTTPMiddleware):
    """Apply request IDs, API-key checks, and a bounded in-process rate limit."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        request_id = request.headers.get("X-Request-ID") or secrets.token_hex(12)
        response: Response
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                request_size = int(content_length)
            except ValueError:
                request_size = max_request_bytes() + 1
            if request_size > max_request_bytes():
                response = Response(
                    content='{"detail":"Request body is too large."}',
                    status_code=413,
                    media_type="application/json",
                )
                response.headers["X-Request-ID"] = request_id
                return response
        is_api_request = request.url.path.startswith("/api/")
        is_capability_media = request.url.path.startswith("/api/v1/media/")
        if (
            is_api_request
            and not is_capability_media
            and request.method != "OPTIONS"
        ):
            keys = api_keys()
            supplied = request.headers.get("X-API-Key", "")
            if api_key_required() and (not keys or supplied not in keys):
                response = Response(
                    content='{"detail":"API key required."}',
                    status_code=401,
                    media_type="application/json",
                )
                response.headers["WWW-Authenticate"] = "ApiKey"
            else:
                client = request.client.host if request.client else "unknown"
                now = time.monotonic()
                limit, window = configured_rate_limit()
                with _rate_lock:
                    timestamps = [
                        stamp for stamp in _rate_windows.get(client, []) if stamp > now - window
                    ]
                    if len(timestamps) >= limit:
                        _rate_windows[client] = timestamps
                        response = Response(
                            content='{"detail":"Rate limit exceeded."}',
                            status_code=429,
                            media_type="application/json",
                        )
                        response.headers["Retry-After"] = str(window)
                    else:
                        timestamps.append(now)
                        _rate_windows[client] = timestamps
                        response = await call_next(request)
        else:
            response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response


app = FastAPI(title="Instagram Fake Account Detector API", version="1.0.0")
app.add_middleware(ProductionBoundaryMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="fake-account-detector")


@app.get("/ready", response_model=HealthResponse)
def ready() -> HealthResponse:
    """Verify the service and required profile model can serve analysis."""
    try:
        load_model()
    except (FileNotFoundError, OSError, ValueError) as exc:
        LOGGER.error("Readiness check failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Model is not ready.") from exc
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


def _frontend_file(path: str = "") -> FileResponse:
    """Serve a built frontend file or the SPA entry point from the same origin."""
    index = FRONTEND_DIST / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=503, detail="Frontend assets are not ready.")
    requested = (FRONTEND_DIST / path).resolve()
    try:
        requested.relative_to(FRONTEND_DIST.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Frontend asset not found.") from exc
    if requested.is_file():
        return FileResponse(requested)
    return FileResponse(index)


@app.get("/", include_in_schema=False)
def frontend_root() -> FileResponse:
    return _frontend_file()


@app.get("/{path:path}", include_in_schema=False)
def frontend_spa(path: str) -> FileResponse:
    return _frontend_file(path)


__all__ = [
    "app",
    "Profile",
    "ProfileAnalysisRequest",
    "BatchAnalysisRequest",
    "BatchAnalysisResponse",
    "PostAnalysisRequest",
]
