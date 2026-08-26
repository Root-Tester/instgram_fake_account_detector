import streamlit as st

from model_loader import load_model
from predictor import predict_profile
from ui import render_inputs, render_prediction_results

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
        padding-top: 16px;
        padding-bottom: 16px;
    }

    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 12px;
            padding-right: 12px;
        }
        .stButton button { width: 100%; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

model = load_model()
profiles = render_inputs()

if profiles:
    st.info(f"Batch ready: {len(profiles)} profile(s) loaded. Click below to run the analysis.")

    if st.button("Analyze Batch", type="primary", use_container_width=True):
        with st.spinner("Analyzing profiles..."):
            results = [predict_profile(model, profile_data) for profile_data in profiles]

        for profile_number, (result, profile_data) in enumerate(zip(results, profiles), start=1):
            render_prediction_results(result, profile_data, profile_number)

st.markdown("---")
st.caption("Model trained on real Instagram data. For research and safety use only.")
