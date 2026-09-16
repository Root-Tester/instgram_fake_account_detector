from functools import lru_cache
import xgboost as xgb
from instgram_fake_account_detector.config import MODEL_PATH


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    model = xgb.Booster()
    model.load_model(str(MODEL_PATH))
    return model
