"""Offline-first enrichment and unsupervised analysis for profile batches."""

from __future__ import annotations

import base64
import hashlib
import io
import math
from collections.abc import Iterable
from typing import Any, Protocol

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class ReverseImageSearchProvider(Protocol):
    """Adapter contract for an external reverse-image-search service."""

    def search(self, image: bytes) -> dict[str, Any]:
        """Return provider evidence, without changing the detector schema."""


def _number(value: Any) -> float:
    try:
        return max(float(value), 0.0)
    except (TypeError, ValueError):
        return 0.0


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return []


def _image_bytes(profile: dict[str, Any]) -> bytes | None:
    value = profile.get("image_bytes") or profile.get("_image_bytes")
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        try:
            return base64.b64decode(value, validate=True)
        except (ValueError, UnicodeDecodeError):
            return None
    return None


def analyze_image(profile: dict[str, Any]) -> dict[str, Any]:
    """Extract transparent local image signals; no image is sent over the network."""
    image = _image_bytes(profile)
    if not image:
        return {"image_available": False, "image_risk": 0.0, "image_sha256": None}

    result: dict[str, Any] = {
        "image_available": True,
        "image_bytes": len(image),
        "image_sha256": hashlib.sha256(image).hexdigest(),
        "image_risk": 0.0,
    }
    try:
        from PIL import Image, ImageStat

        with Image.open(io.BytesIO(image)) as opened:
            image_object = opened.convert("RGB")
            width, height = image_object.size
            result.update({"image_width": width, "image_height": height})
            risk = 0.0
            if width < 80 or height < 80:
                risk += 0.35
            if width == height:
                risk += 0.05
            brightness, contrast = ImageStat.Stat(image_object).mean[0], ImageStat.Stat(image_object).stddev[0]
            result.update({"image_brightness": round(brightness, 2), "image_contrast": round(contrast, 2)})
            if contrast < 8:
                risk += 0.2
            result["image_risk"] = min(risk, 1.0)
    except (ImportError, OSError, ValueError):
        result["image_analysis_error"] = "Install Pillow to inspect image dimensions and quality."

    return result


def analyze_reverse_image(profile: dict[str, Any], provider: ReverseImageSearchProvider | None = None) -> dict[str, Any]:
    """Use supplied evidence or an explicitly configured provider; never scrape implicitly."""
    evidence = profile.get("reverse_image_search", profile.get("reverse_image_matches", []))
    if provider is not None and _image_bytes(profile):
        evidence = provider.search(_image_bytes(profile) or b"")

    if isinstance(evidence, dict):
        matches = _as_list(evidence.get("matches"))
        exact_matches = _number(evidence.get("exact_matches", len(matches)))
        stock_matches = _number(evidence.get("stock_matches", 0))
    else:
        matches = _as_list(evidence)
        exact_matches = float(len(matches))
        stock_matches = 0.0

    risk = min(1.0, exact_matches * 0.2 + stock_matches * 0.15)
    return {
        "reverse_image_matches": int(exact_matches),
        "reverse_image_stock_matches": int(stock_matches),
        "reverse_image_risk": round(risk, 3),
        "reverse_image_search_configured": bool(matches or provider),
    }


def analyze_network(profile: dict[str, Any]) -> dict[str, Any]:
    """Calculate graph and wallet risk from user-supplied, auditable observations."""
    connections = _as_list(profile.get("network_connections", profile.get("linked_accounts", [])))
    blockchain = profile.get("blockchain", {})
    if not isinstance(blockchain, dict):
        blockchain = {}
    transactions = _as_list(blockchain.get("transactions", profile.get("transactions", [])))
    wallet = str(blockchain.get("wallet_address", profile.get("wallet_address", ""))).strip()
    suspicious_transactions = sum(
        1 for transaction in transactions
        if isinstance(transaction, dict) and (
            transaction.get("is_suspicious") or transaction.get("risk") in {"high", "critical"}
        )
    )
    unique_connections = len({str(connection).strip().lower() for connection in connections if str(connection).strip()})
    network_risk = min(1.0, suspicious_transactions * 0.25 + (0.15 if unique_connections == 0 and connections else 0))
    blockchain_risk = min(1.0, suspicious_transactions * 0.3 + (0.1 if wallet and not transactions else 0))
    return {
        "network_connections": unique_connections,
        "network_components": int(_number(profile.get("network_components", 1 if connections else 0))),
        "network_risk": round(network_risk, 3),
        "wallet_present": bool(wallet),
        "blockchain_transactions": len(transactions),
        "blockchain_suspicious_transactions": suspicious_transactions,
        "blockchain_risk": round(blockchain_risk, 3),
    }


def _unsupervised_features(profile: dict[str, Any], supervised: dict[str, Any], image: dict[str, Any], reverse: dict[str, Any], network: dict[str, Any]) -> list[float]:
    return [
        math.log1p(_number(profile.get("followers"))),
        math.log1p(_number(profile.get("followees"))),
        math.log1p(_number(profile.get("mediacount"))),
        _number(profile.get("followees")) / (_number(profile.get("followers")) + 1),
        _number(profile.get("mediacount")) / (_number(profile.get("followers")) + 1),
        float(supervised["probability_fake"]),
        float(image["image_risk"]),
        float(reverse["reverse_image_risk"]),
        float(network["network_risk"]),
        float(network["blockchain_risk"]),
    ]


def _cluster_label(cluster_id: int, profiles: list[dict[str, Any]], indices: list[int]) -> str:
    if cluster_id == -1:
        return "outlier"
    usernames = [str(profiles[index].get("username", "unknown")) for index in indices]
    return f"cluster-{cluster_id}: {', '.join(usernames[:3])}"


def analyze_profiles(
    model: Any,
    profiles: list[dict[str, Any]],
    reverse_image_provider: ReverseImageSearchProvider | None = None,
) -> list[dict[str, Any]]:
    """Combine supervised, enrichment, anomaly, cluster, and final category signals."""
    from instgram_fake_account_detector.predictor import predict_profile

    results: list[dict[str, Any]] = []
    vectors: list[list[float]] = []
    for profile in profiles:
        supervised = predict_profile(model, profile)
        image = analyze_image(profile)
        reverse = analyze_reverse_image(profile, reverse_image_provider)
        network = analyze_network(profile)
        vectors.append(_unsupervised_features(profile, supervised, image, reverse, network))
        results.append({**supervised, "image_analysis": image, "reverse_image_analysis": reverse, "network_analysis": network})

    matrix = StandardScaler().fit_transform(np.asarray(vectors, dtype=float)) if len(vectors) > 1 else np.asarray(vectors, dtype=float)
    if len(results) > 1:
        anomaly_model = IsolationForest(random_state=42, contamination="auto").fit(matrix)
        anomaly_values = -anomaly_model.decision_function(matrix)
        labels = DBSCAN(eps=1.35, min_samples=2).fit_predict(matrix)
    else:
        anomaly_values = np.array([0.0])
        labels = np.array([0])

    groups: dict[int, list[int]] = {}
    for index, label in enumerate(labels):
        groups.setdefault(int(label), []).append(index)
    for index, result in enumerate(results):
        anomaly_score = float(np.clip((anomaly_values[index] + 0.5), 0.0, 1.0))
        evidence_risk = max(
            result["probability_fake"],
            result["image_analysis"]["image_risk"],
            result["reverse_image_analysis"]["reverse_image_risk"],
            result["network_analysis"]["network_risk"],
            result["network_analysis"]["blockchain_risk"],
            anomaly_score,
        )
        if result["network_analysis"]["blockchain_risk"] >= 0.75:
            category = "blockchain-risk"
        elif result["reverse_image_analysis"]["reverse_image_risk"] >= 0.6:
            category = "image-impersonation-risk"
        elif evidence_risk >= 0.65:
            category = "likely-fake-or-bot"
        else:
            category = "lower-risk"
        result.update({
            "anomaly_score": round(anomaly_score, 3),
            "cluster_id": int(labels[index]),
            "cluster_label": _cluster_label(int(labels[index]), profiles, groups[int(labels[index])]),
            "classification": category,
            "risk_score": round(float(evidence_risk), 3),
        })
    return results
