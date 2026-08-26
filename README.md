# Instagram Fake Account Detector

This project is a Streamlit-based application that predicts whether an Instagram profile looks fake or real using a trained XGBoost model.

The detector uses metadata such as:
- follower and following counts
- media counts
- private and verified flags
- profile image and URL presence
- username and biography properties
- a few derived ratio features

It also runs a separate advanced analysis layer alongside the supervised model:
- local image quality and SHA-256 signals (images are not sent anywhere)
- optional reverse-image-search evidence supplied by an adapter or JSON field
- network and blockchain wallet/transaction risk signals
- unsupervised Isolation Forest anomaly scoring
- DBSCAN account clusters calculated across the submitted batch

The Post Analysis tab produces an evidence report for a public Instagram post. It detects likely news, job, offer, and crypto/payment claims; searches public web sources and configured official domains; lists proof links and the basis for its risk score; and extracts wallet addresses for explorer review. It reports confidence and limitations instead of presenting an automated verdict as fact.

Post content also supports supervised training. The optional model uses TF-IDF word n-grams and balanced logistic regression over human-labeled post text. Create a JSONL, JSON list, or JSON mapping with `text` (or `caption`) and `label` (real/ fake, 0/1), then run:

```bash
./.venv/bin/python train_post_model.py labeled_posts.jsonl --output post_content_model.joblib
```

The script prints held-out accuracy, ROC AUC, and a classification report. When `post_content_model.joblib` exists, Post Analysis displays its fake probability and combines it with the transparent content rules. A model trained on a small or biased dataset is not reliable; use independently reviewed examples and keep real and fake classes represented.

The repository includes `post_training_dataset.jsonl` with 50,000 synthetic development rows and `generate_post_dataset.py` to reproduce it. It is balanced between 25,000 real-appearing and 25,000 fake-appearing template examples. Its perfect validation score reflects the artificial templates, not real-world performance; replace it with independently reviewed post data before making operational decisions.

Blockchain data cannot identify the person behind a wallet or prove that an image was first posted on Instagram. The report links to explorers and records these limitations. Proving image provenance requires a registered hash/provenance record from an external service, which this app does not invent.

The original XGBoost model remains compatible with its 19 trained features. Advanced signals are combined after supervised inference, so enrichment does not silently change the meaning of the shipped model.

It is designed as a lightweight batch-analysis tool for reviewing one or many profile records.

## Project structure

- `app.py` — Streamlit entry point
- `ui.py` — input form and prediction rendering logic
- `predictor.py` — feature extraction and per-profile prediction
- `model_loader.py` — loads the trained XGBoost model
- `train_model.py` — trains the model and produces the model artifact
- `data_io.py` — JSON parsing and normalization helpers
- `validators.py` — input validation and schema checks
- `config.py` — file paths and feature columns
- `sample.json` — demo JSON input for testing the batch pipeline
- `sdk.py` — Python SDK wrapper for embedding or calling the model from code

## How it works

1. User enters profile data as JSON, uploads a JSON file, or loads `sample.json`.
2. The app normalizes and validates the incoming profile(s).
3. The model converts the profile data into engineered features.
4. The model returns a probability score and a fake/real verdict.
5. The UI shows the output for each profile in batch mode.

## Run the app

From the project directory:

```bash
cd /workspaces/codespaces-blank/instgram-fake-account-detector
./.venv/bin/python -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8502
```

Open the browser at:

```text
http://127.0.0.1:8502
```

## Quality checks

Install the development dependencies and run the same checks used by GitHub Actions:

```bash
./.venv/bin/python -m pip install -r requirements-dev.txt
./.venv/bin/python -m pylint --rcfile=.pylintrc *.py
./.venv/bin/python -m pytest -q
```

The `n8n/github-quality-dispatch.json` export provides an optional webhook that
dispatches the GitHub quality workflow. See `n8n/README.md` for token and webhook
security setup.

## Sample input format

Single object:

```json
{
  "username": "sample_user",
  "full_name": "Sample User",
  "biography": "This account has a real profile and a short biography.",
  "external_url": "https://example.com",
  "profile_pic_url": "https://example.com/profile.jpg",
  "followers": 150,
  "followees": 180,
  "mediacount": 25,
  "posts_count": 25,
  "stories_count": 3,
  "is_private": false,
  "is_verified": false
}
```

Array of profiles:

```json
[
  {
    "username": "sample_user",
    "followers": 150,
    "followees": 180,
    "mediacount": 25,
    "is_private": false,
    "is_verified": false
  },
  {
    "username": "another_user",
    "followers": 2500,
    "followees": 400,
    "mediacount": 90,
    "is_private": true,
    "is_verified": false
  }
]
```

## Advanced analysis input

Optional fields can be added to any profile. `image_bytes` may contain base64-encoded image data, while the Streamlit app can attach local image uploads automatically. Reverse-image evidence can be supplied by a trusted integration:

```json
{
  "wallet_address": "0x...",
  "blockchain": {
    "wallet_address": "0x...",
    "transactions": [{"is_suspicious": true, "risk": "high"}]
  },
  "network_connections": ["related_account_1", "related_account_2"],
  "reverse_image_search": {
    "matches": ["https://example.com/match"],
    "exact_matches": 1,
    "stock_matches": 0
  }
}
```

For live reverse-image services, implement `ReverseImageSearchProvider.search(image: bytes)` and pass it to `FakeProfileDetectorSDK.predict_profile` or `predict_batch`. No provider is called implicitly, which keeps local analysis deterministic and avoids sending profile images without consent.

## Python SDK usage

```python
from sdk import FakeProfileDetectorSDK

sdk = FakeProfileDetectorSDK()

profile = {
    "username": "sample_user",
    "full_name": "Sample User",
    "biography": "This account has a real profile and a short biography.",
    "external_url": "https://example.com",
    "profile_pic_url": "https://example.com/profile.jpg",
    "followers": 150,
    "followees": 180,
    "mediacount": 25,
    "posts_count": 25,
    "stories_count": 3,
    "is_private": False,
    "is_verified": False,
}

result = sdk.predict_profile(profile)
print(result)
```

Batch prediction:

```python
profiles = [profile, profile]
results = sdk.predict_batch(profiles)
print(results)
```

Load profiles from a file:

```python
results = sdk.predict_file("/path/to/profiles.json")
print(results)
```

## SDK API

### `FakeProfileDetectorSDK(model_path: str | None = None)`
Creates the detector SDK and loads the model from the default project model file unless a custom path is supplied.

### `predict_profile(profile: dict) -> dict`
Returns a single prediction object with supervised and advanced fields:
- `probability_fake`
- `is_fake`
- `confidence`
- `anomaly_score`
- `cluster_id` and `cluster_label`
- `classification` and combined `risk_score`
- `image_analysis`, `reverse_image_analysis`, and `network_analysis`

### `predict_batch(profiles: list[dict]) -> list[dict]`
Runs predictions for each profile and returns a list of result dictionaries.

### `predict_file(file_path: str) -> list[dict]`
Reads a JSON file containing either one profile object or an array of profile objects and returns predictions.

## Important limitations

This application is an evidence-ranking tool, not a definitive identity or fraud service. Network, blockchain, and reverse-image results are only as reliable as the supplied data or integration provider. Unsupervised clusters describe similarity within the submitted batch; they are not verified scam groups. The app does not bypass platform access controls or scrape private accounts.

Because of that, results are best treated as a heuristic signal rather than a definitive real-world verdict.

## Model notes

The project includes a training script that evaluates the model on a held-out dataset. The reported in-sample validation metrics are very high, but they do not guarantee equivalent performance on fresh real-world Instagram accounts outside the same data distribution.
