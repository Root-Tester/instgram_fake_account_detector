from pathlib import Path
import xgboost as xgb
import streamlit as st
from config import MODEL_PATH

@st.cache_resource
def load_model():
    if not MODEL_PATH.exists():
        st.error(f"Model not found: {MODEL_PATH}")
        st.stop()

    model = xgb.Booster()
    model.load_model(str(MODEL_PATH))
    return model
