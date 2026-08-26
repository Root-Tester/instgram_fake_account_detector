import streamlit as st
import matplotlib.pyplot as plt

from post_analysis import analyze_post
from config import SAMPLE_PATH
from data_io import load_json_file, load_json_from_text, load_sample_json, normalize_profiles
from validators import PROFILE_EXAMPLE, validate_profile_data


def _render_sidebar_help() -> None:
    with st.sidebar:
        st.header("How to use")
        st.write(
            "Paste raw JSON, upload one or more JSON files, or load sample.json. "
            "Each payload can be a single profile object or an array of profile objects."
        )
        st.markdown(
            "- `username`: Instagram handle\n"
            "- `followers`, `followees`, `mediacount`: numeric counts\n"
            "- `is_private`, `is_verified`: booleans\n"
            "- optional fields: `biography`, `external_url`, `profile_pic_url`, `posts_count`, `stories_count`"
        )
        st.write("Missing numeric fields default to 0, and missing booleans default to False.")
        with st.expander("Expected JSON template", expanded=True):
            st.json(PROFILE_EXAMPLE)


def _validate_profiles(profiles: list[dict]) -> list[dict] | None:
    for index, profile_data in enumerate(profiles, start=1):
        errors, warnings = validate_profile_data(profile_data)

        if errors:
            for error in errors:
                st.error(f"Profile {index}: {error}")
            return None

        for warning in warnings:
            st.warning(f"Profile {index}: {warning}")

    st.success(f"Loaded {len(profiles)} profile{'s' if len(profiles) != 1 else ''} for batch analysis.")
    return profiles


def render_inputs() -> list[dict] | None:
    _render_sidebar_help()
    tab1, tab2, tab3 = st.tabs(["Paste JSON", "Upload File", "sample.json"])
    payload = None

    with tab1:
        json_input = st.text_area("Paste your JSON:", height=250)
        if json_input.strip():
            try:
                payload = load_json_from_text(json_input)
                st.success("JSON loaded.")
            except Exception as exc:
                st.error(f"Invalid JSON: {exc}")

    with tab2:
        uploaded_files = st.file_uploader(
            "Upload one or more .json files",
            type=["json"],
            accept_multiple_files=True,
            help="Upload a single profile JSON object or a JSON array with several profile objects.",
        )

        if uploaded_files:
            batch_profiles: list[dict] = []
            for uploaded_file in uploaded_files:
                try:
                    file_payload = load_json_file(uploaded_file)
                    profile_batch = normalize_profiles(file_payload)
                    batch_profiles.extend(profile_batch)
                    st.success(f"Loaded {len(profile_batch)} profile(s) from {uploaded_file.name}.")
                except Exception as exc:
                    st.error(f"Error reading {uploaded_file.name}: {exc}")

            if batch_profiles:
                payload = batch_profiles

    with tab3:
        if SAMPLE_PATH.exists():
            if st.checkbox("Load sample.json", value=False):
                try:
                    payload = load_sample_json()
                    st.success("Loaded sample.json.")
                    st.json(payload, expanded=False)
                except Exception as exc:
                    st.error(f"Failed to load sample file: {exc}")
        else:
            st.info("`sample.json` was not found. Add it to enable auto-load.")

    if payload is None:
        return None

    try:
        profiles = normalize_profiles(payload)
    except ValueError as exc:
        st.error(str(exc))
        return None

    validated_profiles = _validate_profiles(profiles)
    if validated_profiles is None:
        return None

    return validated_profiles


def render_post_analysis() -> None:
    st.subheader("Post Analysis")
    st.write("Research a public Instagram post, reel, or video URL using available public metadata and search providers.")
    post_url = st.text_input(
        "Instagram post link",
        placeholder="https://www.instagram.com/p/POST_ID/",
        help="Only public pages that Instagram makes available without login can be analyzed.",
    )
    st.caption("Online research uses bounded public requests. Private posts, login walls, and platform controls are not bypassed.")
    if st.button("Run Post Analysis", type="primary", disabled=not post_url.strip(), use_container_width=True):
        with st.spinner("Fetching public post metadata and researching sources..."):
            try:
                result = analyze_post(post_url)
            except ValueError as exc:
                st.error(str(exc))
                return

        post = result["post"]
        if not post.get("accessible"):
            st.error(post.get("error", "The public post metadata was unavailable."))
            st.json(result)
            return

        col1, col2, col3 = st.columns(3)
        col1.metric("Research status", result["research_status"].title())
        col2.metric("Wallets found", len(result["blockchain"]["addresses_found"]))
        col3.metric("Image risk", f"{result['image_analysis'].get('image_risk', 0):.1%}")

        report = result["report"]
        st.subheader("Evidence Report")
        report_col1, report_col2, report_col3 = st.columns(3)
        report_col1.metric("Assessment", report["verdict"].replace("-", " ").title())
        report_col2.metric("Risk score", f"{report['risk_score']:.1%}")
        report_col3.metric("Confidence", report["confidence"].title())
        st.info(report["basis"])
        if report["claims_detected"] != ["general-claim"]:
            st.write("Claim types detected: " + ", ".join(report["claims_detected"]))

        with st.expander("Proof and source trail", expanded=True):
            for item in report["proof"]:
                source = item.get("source")
                source_text = f" ([source]({source}))" if source else ""
                st.markdown(f"- **{item['effect']}**: {item['finding']}{source_text}")

        with st.expander("Official-source verification", expanded=True):
            official_groups = report["official_source_verification"]
            if not official_groups:
                st.info("No job, offer, payment, or news claim was detected in the public caption.")
            for group in official_groups:
                st.markdown(f"**{group['claim_type']}**")
                for engine in group["sources"]:
                    if not engine.get("configured"):
                        st.caption(engine.get("note", f"{engine['provider']} is not configured."))
                    for item in engine.get("results", []):
                        st.markdown(f"- [{item.get('title') or item.get('url')}]({item.get('url')}) ({engine['provider']})")

        with st.expander("Image provenance and blockchain trace", expanded=True):
            st.json({
                "Image provenance": report["image_provenance"],
                "Blockchain": result["blockchain"],
                "Limitations": report["limitations"],
            })

        if post.get("image_url"):
            st.image(post["image_url"], caption="Public post image", width="stretch")
        st.markdown(f"**{post.get('title') or 'Instagram post'}**")
        st.write(post.get("description") or "No public caption metadata was available.")

        with st.expander("Deep research sources", expanded=True):
            for engine in result["search_engines"]:
                st.markdown(f"**{engine['provider']}**")
                if engine.get("error"):
                    st.warning(engine["error"])
                elif not engine.get("configured"):
                    st.info(engine.get("note", "Provider is not configured."))
                for item in engine.get("results", []):
                    st.markdown(f"- [{item.get('title') or item.get('url')}]({item.get('url')})")

        with st.expander("Reverse image search", expanded=True):
            if result["reverse_image_links"]:
                st.write("Open these provider searches to compare the public image across the web:")
                for item in result["reverse_image_links"]:
                    st.markdown(f"- [{item['provider']}]({item['url']})")
            else:
                st.info("No public image URL was available for reverse-image research.")

        with st.expander("Blockchain source tracing", expanded=True):
            st.json(result["blockchain"])


def render_prediction_results(result: dict, profile_data: dict, profile_number: int | None = None) -> None:
    prob = result["probability_fake"]
    is_fake = result["is_fake"]
    conf = result["confidence"]

    title = f"Profile {profile_number}: Prediction" if profile_number is not None else "Prediction"
    st.subheader(title)
    col1, col2, col3 = st.columns(3)
    col1.metric("Fake Probability", f"{prob:.1%}")
    col2.metric(
        "Verdict",
        "FAKE" if is_fake else "REAL",
        delta="High Risk" if is_fake and conf == "High" else None,
    )
    col3.metric("Confidence", conf)

    st.caption(
        f"Classification: {result.get('classification', 'supervised-only')} | "
        f"Risk score: {result.get('risk_score', prob):.1%} | "
        f"Cluster: {result.get('cluster_label', 'not calculated')}"
    )

    fig, ax = plt.subplots(figsize=(8, 1.5))
    ax.barh(0, prob, color="#ff4b4b" if is_fake else "#4ade80", height=0.6)
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.5, 1])
    ax.set_xticklabels(["0%", "50%", "100%"])
    ax.set_yticks([])
    ax.set_title("Fake Likelihood")
    st.pyplot(fig)

    with st.expander("Profile Summary", expanded=True):
        summary = {
            "Username": profile_data.get("username", "N/A"),
            "Full Name": profile_data.get("full_name", "N/A"),
            "Followers": int(profile_data.get("followers", 0)),
            "Following": int(profile_data.get("followees", 0)),
            "Posts": int(profile_data.get("mediacount", 0)),
            "Stories": int(profile_data.get("stories_count", 0)),
            "Private": "Yes" if profile_data.get("is_private") else "No",
            "Verified": "Yes" if profile_data.get("is_verified") else "No",
            "Has Link": bool(profile_data.get("external_url")),
            "Has Bio": len(str(profile_data.get("biography", ""))) > 10,
        }
        st.json(summary)

    with st.expander("Advanced evidence", expanded=False):
        st.json({
            "Anomaly score": result.get("anomaly_score", 0),
            "Cluster ID": result.get("cluster_id"),
            "Image analysis": result.get("image_analysis", {}),
            "Reverse image analysis": result.get("reverse_image_analysis", {}),
            "Network analysis": result.get("network_analysis", {}),
        })

    if is_fake:
        st.error("**High risk of being fake or bot.**")
    else:
        st.success("**Profile appears legitimate.**")
