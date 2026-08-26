# Instagram Fake Account Detector

This project is a Streamlit-based application that predicts whether an Instagram profile looks fake or real using a trained XGBoost model.

The detector uses metadata such as:
- follower and following counts
- media counts
- private and verified flags
- profile image and URL presence
- username and biography properties
- a few derived ratio features

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
Returns a single prediction object with:
- `probability_fake`
- `is_fake`
- `confidence`

### `predict_batch(profiles: list[dict]) -> list[dict]`
Runs predictions for each profile and returns a list of result dictionaries.

### `predict_file(file_path: str) -> list[dict]`
Reads a JSON file containing either one profile object or an array of profile objects and returns predictions.

## Important limitations

This application is a metadata-based detector, not a full social-media intelligence system. It does not inspect:
- the actual followers and followees network
- the content of posts and captions
- the identity or authenticity of images
- engagement quality or comment behavior
- account history or activity timing

Because of that, results are best treated as a heuristic signal rather than a definitive real-world verdict.

## Model notes

The project includes a training script that evaluates the model on a held-out dataset. The reported in-sample validation metrics are very high, but they do not guarantee equivalent performance on fresh real-world Instagram accounts outside the same data distribution.
