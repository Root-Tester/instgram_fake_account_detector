import streamlit as st

from instgram_fake_account_detector.model_loader import load_model
from instgram_fake_account_detector.advanced_analysis import analyze_profiles
from instgram_fake_account_detector.ui import render_inputs, render_post_analysis, render_prediction_results

st.set_page_config(
    page_title="Fake Profile Detector",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("**Detect fake Instagram profiles using AI.**")
st.markdown(
    """
    <style>
    .main .block-container {
        max-width: 1100px;
        padding: 1rem clamp(0.75rem, 3vw, 2rem) 1.5rem;
        width: 100%;
        box-sizing: border-box;
    }

    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap;
        gap: 1rem;
    }

    [data-testid="stMetric"] {
        min-width: min(100%, 10rem);
        overflow-wrap: anywhere;
    }

    [data-testid="stImage"] {
        max-width: 100%;
        display: flex;
        justify-content: center;
    }

    [data-testid="stImage"] img {
        width: auto !important;
        max-width: 100%;
        max-height: calc(100dvh - 8rem);
        height: auto;
        object-fit: contain;
    }

    [data-testid="stPlotlyChart"],
    .stPlotlyChart {
        max-width: 100%;
    }

    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 0.75rem;
            padding-bottom: 1rem;
        }

        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }

        [data-testid="stTabs"] [role="tablist"] {
            overflow-x: auto;
            scrollbar-width: thin;
        }

        [data-testid="stTabs"] [role="tab"] {
            flex: 0 0 auto;
            white-space: nowrap;
        }

        .stButton button { width: 100%; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

model = load_model()
account_tab, post_tab = st.tabs(["Account Analysis", "Post Analysis"])

with post_tab:
    render_post_analysis()

with account_tab:
    profiles = render_inputs()

    if profiles:
        st.info(f"Batch ready: {len(profiles)} profile(s) loaded. Click below to run the analysis.")

        if st.button("Analyze Batch", type="primary", use_container_width=True):
            with st.spinner("Analyzing profiles..."):
                results = analyze_profiles(model, profiles)

            for profile_number, (result, profile_data) in enumerate(zip(results, profiles), start=1):
                render_prediction_results(result, profile_data, profile_number)

st.markdown("---")
st.caption("Model trained on real Instagram data. For research and safety use only.")
