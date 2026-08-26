import json
import numpy as np
import pandas as pd
import xgboost as xgb
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from instgram_fake_account_detector.config import MODEL_PATH, PROFILE_DATA_PATH

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)

# ==============================
# LOAD DATASET
# ==============================

with PROFILE_DATA_PATH.open("r", encoding="utf-8") as f:
    raw = json.load(f)

# Dataset is stored as {"01": {...}, "02": {...}}
df = pd.DataFrame(raw.values())

print(f"Loaded {len(df)} profiles")

# ==============================
# REQUIRED COLUMNS
# ==============================

string_cols = [
    "username",
    "full_name",
    "biography",
    "external_url",
    "profile_pic_url",
]

numeric_cols = [
    "followers",
    "followees",
    "mediacount",
    "posts_count",
    "stories_count",
]

bool_cols = [
    "is_private",
    "is_verified",
]

for col in string_cols:
    if col not in df.columns:
        df[col] = ""

for col in numeric_cols:
    if col not in df.columns:
        df[col] = 0

for col in bool_cols:
    if col not in df.columns:
        df[col] = False

# ==============================
# CLEAN DATA
# ==============================

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

df["is_private"] = df["is_private"].fillna(False).astype(int)
df["is_verified"] = df["is_verified"].fillna(False).astype(int)

df["has_profile_pic"] = df["profile_pic_url"].notna().astype(int)

# ==============================
# FEATURE ENGINEERING
# ==============================

df["follower_followee_ratio"] = (
    df["followers"] / (df["followees"] + 1)
)

df["media_per_follower"] = (
    df["mediacount"] / (df["followers"] + 1)
)

df["followee_per_media"] = (
    df["followees"] / (df["mediacount"] + 1)
)

df["username_length"] = (
    df["username"].astype(str).str.len()
)

df["full_name_length"] = (
    df["full_name"].astype(str).str.len()
)

df["biography_length"] = (
    df["biography"].astype(str).str.len()
)

df["has_external_url"] = (
    df["external_url"].fillna("").astype(str).str.len() > 0
).astype(int)

df["username_digit_count"] = (
    df["username"].astype(str).str.count(r"\d")
)

df["log_followers"] = np.log1p(df["followers"])
df["log_followees"] = np.log1p(df["followees"])
df["log_mediacount"] = np.log1p(df["mediacount"])

FEATURE_COLS = [
    "followers",
    "followees",
    "mediacount",
    "posts_count",
    "stories_count",
    "is_private",
    "is_verified",
    "has_profile_pic",
    "follower_followee_ratio",
    "media_per_follower",
    "followee_per_media",
    "username_length",
    "full_name_length",
    "biography_length",
    "has_external_url",
    "username_digit_count",
    "log_followers",
    "log_followees",
    "log_mediacount",
]

# ==============================
# LABEL
# ==============================

df["is_fake"] = (
    df["is_fake"]
    .astype(str)
    .str.strip()
    .replace({"true": 1, "false": 0})
    .astype(int)
)

X = df[FEATURE_COLS].fillna(0)
y = df["is_fake"]

# ==============================
# TRAIN TEST SPLIT
# ==============================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)

# ==============================
# TRAIN MODEL
# ==============================

model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="binary:logistic",
    eval_metric="logloss",
    random_state=42,
)

model.fit(X_train, y_train)

# ==============================
# EVALUATE
# ==============================

pred = model.predict(X_test)
prob = model.predict_proba(X_test)[:, 1]

print("\n========== RESULTS ==========")

print("Accuracy :", accuracy_score(y_test, pred))
print("Precision:", precision_score(y_test, pred))
print("Recall   :", recall_score(y_test, pred))
print("F1 Score :", f1_score(y_test, pred))
print("ROC AUC  :", roc_auc_score(y_test, prob))

print("\nConfusion Matrix")
print(confusion_matrix(y_test, pred))

# ==============================
# SAVE MODEL
# ==============================

model.get_booster().save_model(str(MODEL_PATH))

print("\nModel saved as fake_profile_model.model")