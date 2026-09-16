import io

from PIL import Image

from instgram_fake_account_detector import post_analysis


class FakeResponse:
    def __init__(self, content, content_type="image/png"):
        self.content = content
        self.headers = {
            "Content-Type": content_type,
            "Content-Length": str(len(content)),
        }

    def raise_for_status(self):
        return None

    def iter_content(self, _chunk_size):
        yield self.content


def _png() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (100, 100), "red").save(output, format="PNG")
    return output.getvalue()


def test_candidate_media_requires_real_image_and_is_bounded(monkeypatch):
    monkeypatch.setattr(
        post_analysis.requests, "get", lambda *args, **kwargs: FakeResponse(_png())
    )
    result = post_analysis.fetch_candidate_media(
        "https://scontent.cdninstagram.com/image.png"
    )
    assert result["available"] is True
    assert result["media_type"] == "image/png"
    assert "_content" not in result

    monkeypatch.setattr(
        post_analysis.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(b"<html>login</html>", "text/html"),
    )
    rejected = post_analysis.fetch_candidate_media(
        "https://scontent.cdninstagram.com/login"
    )
    assert rejected["available"] is False


def test_candidate_media_rejects_logo_and_oversized_responses(monkeypatch):
    monkeypatch.setattr(
        post_analysis.requests, "get", lambda *args, **kwargs: FakeResponse(_png())
    )
    assert not post_analysis.fetch_candidate_media(
        "https://scontent.cdninstagram.com/logo.png"
    )["available"]

    oversized = FakeResponse(_png())
    oversized.headers["Content-Length"] = str(post_analysis.MAX_IMAGE_BYTES + 1)
    monkeypatch.setattr(
        post_analysis.requests, "get", lambda *args, **kwargs: oversized
    )
    assert not post_analysis.fetch_candidate_media(
        "https://scontent.cdninstagram.com/image.png"
    )["available"]


def test_post_analysis_publishes_reference_only_after_validation(monkeypatch):
    monkeypatch.setattr(
        post_analysis,
        "fetch_public_post",
        lambda _url: {
            "url": "https://www.instagram.com/p/abc/",
            "accessible": True,
            "title": "A post",
            "description": "",
            "image_url": "https://scontent.cdninstagram.com/image.png",
        },
    )
    monkeypatch.setattr(
        post_analysis,
        "_fetch_candidate_media",
        lambda _url, include_content=False: {
            "available": True,
            "media_type": "image/png",
            "width": 100,
            "height": 100,
            "sha256": "a" * 64,
            **({"_content": _png()} if include_content else {}),
        },
    )
    monkeypatch.setattr(post_analysis, "search_web", lambda _post: [])
    result = post_analysis.analyze_post("https://www.instagram.com/p/abc/")
    assert result["image_reference"].startswith("/api/v1/media/")
    assert result["post"]["image_reference"] == result["image_reference"]
