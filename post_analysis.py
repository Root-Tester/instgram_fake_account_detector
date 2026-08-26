"""Public Instagram post research with explicit, bounded online providers."""

from __future__ import annotations

import html
import os
import re
from typing import Any
from urllib.parse import quote, urlparse

import requests


USER_AGENT = "FakeProfileDetector/1.0 (public research; contact repository owner)"
TIMEOUT = 12
MAX_SOURCES = 5


def _request(url: str, params: dict[str, str] | None = None) -> requests.Response:
    response = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    response.raise_for_status()
    return response


def validate_post_url(post_url: str) -> str:
    parsed = urlparse(post_url.strip())
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() not in {"instagram.com", "www.instagram.com"}:
        raise ValueError("Enter a public Instagram URL such as https://www.instagram.com/p/POST_ID/.")
    if not re.search(r"/(p|reel|tv)/[A-Za-z0-9_-]+", parsed.path):
        raise ValueError("The URL must point to an Instagram post, reel, or video.")
    return post_url.strip()


def _meta(document: str, name: str) -> str:
    pattern = rf'<meta[^>]+(?:property|name)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']*)'
    match = re.search(pattern, document, flags=re.IGNORECASE)
    if not match:
        pattern = rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']{re.escape(name)}["\']'
        match = re.search(pattern, document, flags=re.IGNORECASE)
    return html.unescape(match.group(1)) if match else ""


def fetch_public_post(post_url: str) -> dict[str, Any]:
    url = validate_post_url(post_url)
    try:
        response = _request(url)
    except requests.RequestException as exc:
        return {"url": url, "accessible": False, "error": f"Public page could not be fetched: {exc}"}

    document = response.text
    image_url = _meta(document, "og:image")
    description = _meta(document, "og:description") or _meta(document, "description")
    title = _meta(document, "og:title")
    canonical = _meta(document, "og:url") or url
    return {
        "url": canonical,
        "accessible": bool(image_url or description or title),
        "title": title,
        "description": description,
        "image_url": image_url,
        "html_bytes": len(response.content),
    }


def _ddg_search(query: str) -> dict[str, Any]:
    try:
        response = _request("https://html.duckduckgo.com/html/", {"q": query})
        matches = re.findall(r'class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', response.text, flags=re.IGNORECASE | re.DOTALL)
        return {
            "provider": "DuckDuckGo",
            "configured": True,
            "results": [{"url": html.unescape(url), "title": re.sub(r"<[^>]+>", "", title)} for url, title in matches[:MAX_SOURCES]],
        }
    except requests.RequestException as exc:
        return {"provider": "DuckDuckGo", "configured": True, "results": [], "error": str(exc)}


def _google_search(query: str) -> dict[str, Any]:
    key, engine = os.getenv("GOOGLE_API_KEY"), os.getenv("GOOGLE_CSE_ID")
    if not key or not engine:
        return {"provider": "Google", "configured": False, "results": [], "note": "Set GOOGLE_API_KEY and GOOGLE_CSE_ID for Google Custom Search."}
    try:
        payload = _request("https://www.googleapis.com/customsearch/v1", {"key": key, "cx": engine, "q": query}).json()
        return {"provider": "Google", "configured": True, "results": [{"url": item.get("link"), "title": item.get("title")} for item in payload.get("items", [])[:MAX_SOURCES]]}
    except (requests.RequestException, ValueError) as exc:
        return {"provider": "Google", "configured": True, "results": [], "error": str(exc)}


def _bing_search(query: str) -> dict[str, Any]:
    key = os.getenv("BING_SEARCH_KEY")
    if not key:
        return {"provider": "Bing", "configured": False, "results": [], "note": "Set BING_SEARCH_KEY for Bing Web Search."}
    try:
        response = requests.get("https://api.bing.microsoft.com/v7.0/search", params={"q": query, "count": MAX_SOURCES}, headers={"Ocp-Apim-Subscription-Key": key, "User-Agent": USER_AGENT}, timeout=TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        return {"provider": "Bing", "configured": True, "results": [{"url": item.get("url"), "title": item.get("name")} for item in payload.get("webPages", {}).get("value", [])]}
    except (requests.RequestException, ValueError) as exc:
        return {"provider": "Bing", "configured": True, "results": [], "error": str(exc)}


def search_web(post: dict[str, Any]) -> list[dict[str, Any]]:
    query = " ".join(part for part in [post.get("title", ""), post.get("description", "")] if part).strip()[:400]
    if not query:
        query = post.get("url", "")
    return [_ddg_search(query), _google_search(query), _bing_search(query)]


def _search_query(post: dict[str, Any], suffix: str = "") -> str:
    text = " ".join(str(post.get(key, "")) for key in ("title", "description"))
    return f"{text[:320]} {suffix}".strip()


def _search_official_sources(post: dict[str, Any], claim_type: str) -> list[dict[str, Any]]:
    """Search restricted official domains; a result is evidence to review, not proof."""
    suffix = {
        "news": "site:gov OR site:gov.uk OR site:who.int OR site:un.org",
        "job-vacancy": "site:gov OR site:gov.uk OR site:linkedin.com/company",
        "offer-or-giveaway": "site:gov OR site:ftc.gov OR site:consumer.ftc.gov",
        "crypto-or-payment": "site:gov OR site:sec.gov OR site:ftc.gov",
    }.get(claim_type, "site:gov")
    query = _search_query(post, suffix)
    providers = [_ddg_search(query), _google_search(query), _bing_search(query)]
    return [
        {**provider, "claim_type": claim_type, "query": query}
        for provider in providers
    ]


def classify_claims(text: str) -> list[str]:
    lowered = text.lower()
    claims: list[str] = []
    patterns = {
        "job-vacancy": r"\b(job|vacancy|hiring|career|recruit|salary|work from home|招聘)\b",
        "offer-or-giveaway": r"\b(offer|discount|giveaway|prize|free|coupon|limited time|winner)\b",
        "news": r"\b(breaking|news|report|official statement|minister|government|earthquake|election)\b",
        "crypto-or-payment": r"\b(crypto|bitcoin|ethereum|wallet|usdt|send money|pay|payment|investment)\b",
    }
    for claim_type, pattern in patterns.items():
        if re.search(pattern, lowered):
            claims.append(claim_type)
    return claims or ["general-claim"]


def _flatten_sources(search_engines: list[dict[str, Any]]) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    for engine in search_engines:
        for item in engine.get("results", []):
            if item.get("url"):
                sources.append({"provider": str(engine.get("provider", "search")), "title": str(item.get("title", "")), "url": str(item["url"])})
    return sources


def build_post_report(result: dict[str, Any]) -> dict[str, Any]:
    """Create an auditable report from collected observations and source links."""
    post = result.get("post", {})
    text = " ".join(str(post.get(key, "")) for key in ("title", "description"))
    claims = classify_claims(text)
    sources = _flatten_sources(result.get("search_engines", []))
    image = result.get("image_analysis", {})
    blockchain = result.get("blockchain", {})
    evidence: list[dict[str, Any]] = [
        {
            "finding": "Public Instagram metadata was retrieved" if post.get("accessible") else "Public Instagram metadata was not retrieved",
            "effect": "supports-observation" if post.get("accessible") else "limits-conclusion",
            "source": post.get("url"),
        },
        {
            "finding": f"Image quality risk score: {image.get('image_risk', 0):.1%}",
            "effect": "supports-risk" if image.get("image_risk", 0) >= 0.5 else "neutral",
            "source": post.get("image_url"),
        },
        {
            "finding": f"{len(blockchain.get('addresses_found', []))} public wallet address(es) extracted",
            "effect": "supports-verification" if blockchain.get("addresses_found") else "neutral",
            "source": post.get("url"),
        },
    ]
    for source in sources[:MAX_SOURCES]:
        evidence.append({"finding": source["title"] or "Search result found", "effect": "requires-human-review", "source": source["url"], "provider": source["provider"]})

    risk_points = 0.0
    if not post.get("accessible"):
        risk_points += 0.25
    if image.get("image_risk", 0) >= 0.5:
        risk_points += 0.2
    if blockchain.get("addresses_found"):
        risk_points += 0.2
    if any(claim in {"job-vacancy", "offer-or-giveaway", "crypto-or-payment"} for claim in claims):
        risk_points += 0.1
    if sources:
        risk_points -= 0.1
    risk_score = max(0.0, min(1.0, risk_points))
    if risk_score >= 0.6:
        verdict = "likely-fraudulent-or-misleading"
    elif risk_score >= 0.3:
        verdict = "needs-verification"
    else:
        verdict = "no-fraud-proof-found"
    return {
        "verdict": verdict,
        "risk_score": round(risk_score, 3),
        "confidence": "low" if not sources or not post.get("accessible") else "medium",
        "claims_detected": claims,
        "basis": "The verdict is a weighted triage signal based on the listed observations; it is not a legal or factual determination.",
        "proof": evidence,
        "image_provenance": {
            "observed_post_url": post.get("url"),
            "reverse_search_links": result.get("reverse_image_links", []),
            "first_post_proven": False,
            "status": "No public service can establish the first web posting from an Instagram image alone. Blockchain can prove a registered hash or transaction timestamp only when provenance data is supplied.",
        },
        "official_source_verification": result.get("official_source_verification", []),
        "limitations": [
            "Search results are leads and require human review of the linked source.",
            "Absence of an official result does not prove a claim is false.",
            "A wallet address does not identify its owner without lawful attribution evidence.",
        ],
    }


def reverse_image_search_links(image_url: str) -> list[dict[str, str]]:
    if not image_url:
        return []
    encoded = quote(image_url, safe="")
    return [
        {"provider": "Google Lens", "url": f"https://lens.google.com/uploadbyurl?url={encoded}"},
        {"provider": "Bing Visual Search", "url": f"https://www.bing.com/images/searchbyimage?cbir=sbi&imgurl={encoded}"},
        {"provider": "Yandex Images", "url": f"https://yandex.com/images/search?rpt=imageview&url={encoded}"},
    ]


WALLET_PATTERNS = {
    "ethereum": re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
    "bitcoin": re.compile(r"\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,59}\b"),
    "solana": re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b"),
}


def trace_blockchain_sources(text: str) -> dict[str, Any]:
    addresses: list[dict[str, str]] = []
    for chain, pattern in WALLET_PATTERNS.items():
        for address in dict.fromkeys(pattern.findall(text)):
            explorer = {"ethereum": "https://etherscan.io/address/", "bitcoin": "https://www.blockchain.com/explorer/addresses/btc/", "solana": "https://solscan.io/account/"}[chain]
            addresses.append({"chain": chain, "address": address, "explorer_url": explorer + address})
    return {
        "addresses_found": addresses,
        "trace_note": "Addresses are extracted from public text only. Explorer links are provided for human verification; no wallet is attributed to a person automatically.",
    }


def analyze_post(post_url: str) -> dict[str, Any]:
    post = fetch_public_post(post_url)
    if not post.get("accessible"):
        result = {
            "post": post,
            "image_analysis": {"image_available": False, "image_risk": 0.0},
            "search_engines": [],
            "reverse_image_links": [],
            "blockchain": trace_blockchain_sources(post.get("description", "")),
            "official_source_verification": [],
            "research_status": "limited",
        }
        result["report"] = build_post_report(result)
        return result
    combined_text = " ".join(str(post.get(key, "")) for key in ("title", "description", "url"))
    image_analysis: dict[str, Any] = {"image_available": False, "image_risk": 0.0}
    if post.get("image_url"):
        try:
            image_response = _request(post["image_url"])
            from advanced_analysis import analyze_image

            image_analysis = analyze_image({"image_bytes": image_response.content})
        except requests.RequestException as exc:
            image_analysis = {"image_available": False, "image_risk": 0.0, "error": str(exc)}
    claims = classify_claims(combined_text)
    official_sources = [
        {"claim_type": claim, "sources": _search_official_sources(post, claim)}
        for claim in claims
        if claim != "general-claim"
    ]
    result = {
        "post": post,
        "image_analysis": image_analysis,
        "search_engines": search_web(post),
        "reverse_image_links": reverse_image_search_links(post.get("image_url", "")),
        "blockchain": trace_blockchain_sources(combined_text),
        "official_source_verification": official_sources,
        "research_status": "complete" if post.get("image_url") else "partial",
    }
    result["report"] = build_post_report(result)
    return result
