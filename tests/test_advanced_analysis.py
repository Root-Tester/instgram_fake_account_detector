from instgram_fake_account_detector.advanced_analysis import analyze_image, analyze_network, analyze_profiles, analyze_reverse_image
from instgram_fake_account_detector.model_loader import load_model


def test_network_and_reverse_image_evidence_are_scored():
    profile = {
        "username": "test_user",
        "reverse_image_search": {"matches": ["match"], "exact_matches": 2},
        "blockchain": {
            "wallet_address": "0x123",
            "transactions": [{"risk": "high"}],
        },
        "network_connections": ["account_a", "account_b"],
    }

    reverse = analyze_reverse_image(profile)
    network = analyze_network(profile)

    assert reverse["reverse_image_matches"] == 2
    assert reverse["reverse_image_risk"] > 0
    assert network["blockchain_suspicious_transactions"] == 1
    assert network["blockchain_risk"] > 0


def test_base64_image_is_analyzed_without_network_access():
    result = analyze_image({"image_bytes": "aGVsbG8="})

    assert result["image_available"] is True
    assert len(result["image_sha256"]) == 64


def test_batch_analysis_returns_unsupervised_fields():
    profiles = [
        {"username": "one", "followers": 10, "followees": 500},
        {"username": "two", "followers": 500, "followees": 20},
    ]

    results = analyze_profiles(load_model(), profiles)

    assert len(results) == 2
    assert all("anomaly_score" in result for result in results)
    assert all("cluster_id" in result for result in results)