from fastapi.testclient import TestClient

from instgram_fake_account_detector import api
from instgram_fake_account_detector import post_analysis

client = TestClient(api.app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_cors_allows_configured_local_frontend_but_not_unknown_origins():
    allowed = client.options(
        "/api/v1/profiles/analyze",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    denied = client.options(
        "/api/v1/profiles/analyze",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in denied.headers


def test_profile_and_batch_routes_reuse_analysis(monkeypatch):
    def fake_load_model():
        return object()

    monkeypatch.setattr(api, "load_model", fake_load_model)

    def fake_analysis(_model, profiles):
        return [
            {"username": profile["username"], "probability_fake": 0.1}
            for profile in profiles
        ]

    monkeypatch.setattr(api, "analyze_profiles", fake_analysis)
    single = client.post(
        "/api/v1/profiles/analyze", json={"profile": {"username": "one"}}
    )
    batch = client.post(
        "/api/v1/profiles/batch",
        json={"profiles": [{"username": "one"}, {"username": "two"}]},
    )

    assert single.status_code == 200
    assert single.json()["username"] == "one"
    assert batch.status_code == 200
    assert batch.json()["count"] == 2
    assert len(batch.json()["results"]) == 2


def test_post_route_reuses_post_analysis(monkeypatch):
    def fake_post_analysis(url):
        return {"post": {"url": url}, "report": {"risk_score": 0}}

    monkeypatch.setattr(api, "analyze_post", fake_post_analysis)
    response = client.post(
        "/api/v1/posts/analyze", json={"post_url": "https://www.instagram.com/p/abc/"}
    )
    assert response.status_code == 200
    assert response.json()["post"]["url"].endswith("/abc/")


def test_validated_media_endpoint_serves_only_cached_bytes():
    token = post_analysis.publish_validated_media(b"image-bytes", "image/png")
    response = client.get(f"/api/v1/media/{token}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"image-bytes"
    assert client.get("/api/v1/media/unknown-token").status_code == 404


def test_post_request_accepts_legacy_url_alias():
    request = api.PostAnalysisRequest.model_validate(
        {"url": "https://www.instagram.com/p/abc/"}
    )
    assert request.post_url.endswith("/abc/")


def test_batch_contract_matches_react_payload_shape():
    payload = api.BatchAnalysisRequest.model_validate(
        {"profiles": [{"username": "one"}, {"username": "two"}]}
    )
    encoded = api.BatchAnalysisResponse(
        results=[{"username": "one"}, {"username": "two"}], count=2
    )
    assert len(payload.profiles) == 2
    assert encoded.count == 2
    assert encoded.results[0]["username"] == "one"
