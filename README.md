# Instagram Fake Account Detector: AI-Powered Profile and Post Analysis

> Open-source React and FastAPI toolkit for Instagram fake-account detection, post-content analysis, scam-risk triage, and explainable evidence review.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React%20%2B%20FastAPI-app-61DAFB?logo=react&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

**Topics:** Instagram fake account detector, fake post detection, scam detection, bot detection, content analysis, reverse image search, blockchain tracing, supervised learning, unsupervised learning, React, FastAPI.

This project provides a lightweight React frontend and Python FastAPI backend that predict whether an Instagram profile looks fake or real using a trained XGBoost model.

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
PYTHONPATH=backend/app ./.venv/bin/python scripts/train_post_model.py data/posts/labeled_posts.jsonl --output models/post_content_model.joblib
```

The script prints held-out accuracy, ROC AUC, and a classification report. When `post_content_model.joblib` exists, Post Analysis displays its fake probability and combines it with the transparent content rules. A model trained on a small or biased dataset is not reliable; use independently reviewed examples and keep real and fake classes represented.

The repository includes `post_training_dataset.jsonl` with 50,000 synthetic development rows and `generate_post_dataset.py` to reproduce it. It is balanced between 25,000 real-appearing and 25,000 fake-appearing template examples. Its perfect validation score reflects the artificial templates, not real-world performance; replace it with independently reviewed post data before making operational decisions.

Blockchain data cannot identify the person behind a wallet or prove that an image was first posted on Instagram. The report links to explorers and records these limitations. Proving image provenance requires a registered hash/provenance record from an external service, which this app does not invent.

The original XGBoost model remains compatible with its 19 trained features. Advanced signals are combined after supervised inference, so enrichment does not silently change the meaning of the shipped model.

It is designed as a lightweight batch-analysis tool for reviewing one or many profile records.

## Project structure

- **Frontend:** `frontend/` — lightweight Vite/React TypeScript client.
- **Backend:** `backend/app/` — FastAPI entry point, typed routes, analysis services, validators, model loading, and SDK implementation.
- **Database boundary:** `database/` — persistence interfaces and migration placeholders; no concrete database is enabled yet.
- **Models:** `backend/app/instgram_fake_account_detector/model_loader.py`, `post_model.py`, `models/` — supervised model loading and inference.
- **Training:** `scripts/train_profile_model.py`, `scripts/train_post_model.py`, `scripts/generate_post_dataset.py` — reproducible model and dataset workflows.
- **Data:** `data/profiles/`, `data/posts/`; examples live in `examples/`.
- **Integration:** `sdk.py`, `n8n/` — programmatic access and optional automation.
- **Runtime:** `run_api.sh`, `backend/requirements.txt`, `backend/requirements-dev.txt` — local deployment and dependencies.

The root `sdk.py` file is a compatibility shim. The maintained Python package
is under `backend/app/instgram_fake_account_detector/`.

Version 2.0 keeps the repository root as the only project root and separates
ownership by boundary:

```text
backend/    FastAPI application, Python package, tests, and dependencies
database/   persistence interfaces and migration placeholders only
frontend/   React/Vite client
shared/     cross-layer contracts and types
models/     reviewed model artifacts
data/       public/sample/training data
scripts/    training and maintenance commands
infra/      deployment documentation (Render manifest stays at root)
docs/       architecture and operations documentation
```

There is no `backend` database implementation yet and no second folder named
after the repository. The `backend/app/instgram_fake_account_detector/`
directory is the Python import package required by the backend.

## React and FastAPI development

Start both the FastAPI backend and Vite frontend with one command:

```bash
bash run_dev.sh
```

This starts the backend at `http://127.0.0.1:8000` and the Vite frontend at
`http://127.0.0.1:5173`. Press `Ctrl+C` once to stop both processes.

To run them separately:

```bash
bash run_api.sh
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server proxies `/api` requests to `http://localhost:8000`.
For a production-like single-service run, build the frontend with
`cd frontend && npm run build`, then run `bash run_api.sh`; FastAPI serves the
generated `frontend/dist` files and the API on one port.
The post-analysis API validates and caches public image bytes before exposing a
tokenized `/api/v1/media/` reference, so login pages, logos, and HTML responses
are not rendered as post images.

The React frontend is the only UI. The Python package remains available through
the FastAPI API and SDK.

## Render deployment

The repository deploys as one Render Python web service in
[render.yaml](./render.yaml). Render installs the Python dependencies, builds
the React app into `frontend/dist`, and starts FastAPI. FastAPI serves both the
React application and `/api/*` routes from the same origin and Render-provided
dynamic `PORT`. The client never chooses a public port.

Create a Render Blueprint from the repository and apply `render.yaml`. Do not
set `VITE_API_BASE_URL` for this topology; the frontend uses relative,
same-origin API requests. `VITE_API_KEY` is browser-visible by design and is
not a confidential secret.

For production, set `ENVIRONMENT=production`, `REQUIRE_API_KEY=true`, and
configure `API_KEYS` as a Render secret. The frontend's `VITE_API_KEY` is a
browser access token, not a confidential server secret; use a private frontend,
short-lived/revocable keys, and a gateway or user-authentication layer when
strong client identity is required. The opaque validated-media URL remains a
capability URL so browser image requests do not need custom headers.

The included production configuration is intended for a controlled single
instance. The rate limiter and short-lived validated-media cache are process
local; use a shared Redis/object-storage implementation before enabling
multiple API instances or relying on media delivery across restarts.

## How it works

1. User enters profile data as JSON, uploads a JSON file, or loads `sample.json`.
2. The app normalizes and validates the incoming profile(s).
3. The model converts the profile data into engineered features.
4. The model returns a probability score and a fake/real verdict.
5. The UI shows the output for each profile in batch mode.

## Run the app

Start the API from the project directory:

```bash
bash run_api.sh
```

Open the combined application at:

```text
http://127.0.0.1:8000
```

`run_api.sh` binds to `0.0.0.0` and uses the `PORT` environment variable when
provided by a host such as Render. The included `render.yaml` builds and
deploys the API and React application together.

For a configuration-driven Bash launch:

```bash
cp .env.example .env
bash run_api.sh
```

Do not commit `.env`, API keys, private datasets, or user uploads. See [SECURITY.md](SECURITY.md).

## Quality checks

Install the development dependencies and run the same checks used by GitHub Actions:

```bash
./.venv/bin/python -m pip install -r backend/requirements-dev.txt
PYTHONPATH=backend/app ./.venv/bin/python -m pylint --rcfile=backend/.pylintrc backend/app scripts backend/tests
PYTHONPATH=backend/app ./.venv/bin/python -m pytest -q backend/tests
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

Optional fields can be added to any profile. `image_bytes` may contain base64-encoded image data. Reverse-image evidence can be supplied by a trusted integration:

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

To call the Render-hosted backend instead of loading the model locally:

```python
from sdk import FakeProfileDetectorSDK

sdk = FakeProfileDetectorSDK(
    api_base_url="https://instagram-fake-account-detector.onrender.com"
)
print(sdk.health())
result = sdk.predict_profile(profile)
post_report = sdk.analyze_post("https://www.instagram.com/p/example/")
```

The SDK is a Python client for the backend; it does not bundle or serve the
React frontend. The browser frontend and the SDK use the same FastAPI routes,
so profile, batch, post, and health behavior stays consistent across local and
Render deployments.

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



================================================
FILE: LICENSE
================================================
MIT License

Copyright (c) 2026 Tushar Kumar 

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.



================================================
FILE: render.yaml
================================================
# One web service builds and serves both the frontend and API on Render's dynamic PORT.
services:
  - type: web
    name: instagram-fake-account-detector-api
    runtime: python
    plan: starter
    buildCommand: pip install -r backend/requirements.txt && npm ci --prefix frontend && npm run build --prefix frontend
    startCommand: bash run_api.sh
    healthCheckPath: /ready
    envVars:
      - key: PYTHON_VERSION
        value: "3.13.0"
      - key: FRONTEND_ORIGINS
        value: https://instagram-fake-account-detector-frontend.onrender.com
      - key: ENVIRONMENT
        value: production
      - key: REQUIRE_API_KEY
        value: "true"
      - key: API_KEYS
        sync: false
      - key: RATE_LIMIT_REQUESTS
        value: "120"
      - key: RATE_LIMIT_WINDOW_SECONDS
        value: "60"
      - key: MAX_REQUEST_BYTES
        value: "262144"
      - key: VITE_API_KEY
        sync: false



================================================
FILE: run_api.sh
================================================
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
export PYTHONPATH="$PWD/backend/app${PYTHONPATH:+:$PYTHONPATH}"

if [[ -f .env ]]; then
	set -a
	. ./.env
	set +a
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
if [[ -x .venv/bin/python && -z "${PYTHON_BIN_OVERRIDE:-}" ]]; then
	PYTHON_BIN=".venv/bin/python"
fi

exec "$PYTHON_BIN" -m uvicorn backend.app.main:app \
	--host "${HOST:-0.0.0.0}" \
	--port "${PORT:-8000}"



================================================
FILE: run_dev.sh
================================================
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  trap - INT TERM EXIT
  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  wait "$FRONTEND_PID" "$BACKEND_PID" 2>/dev/null || true
}

trap cleanup INT TERM EXIT

cd "$ROOT_DIR"
bash run_api.sh &
BACKEND_PID=$!

(
  cd "$ROOT_DIR/frontend"
  exec npm run dev
) &
FRONTEND_PID=$!

wait -n "$BACKEND_PID" "$FRONTEND_PID"
exit $?



================================================
FILE: sdk.py
================================================
"""Compatibility import for the packaged SDK."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend" / "app"))

from instgram_fake_account_detector.sdk import FakeProfileDetectorSDK

__all__ = ["FakeProfileDetectorSDK"]



================================================
FILE: SECURITY.md
================================================
# Security Policy

## Scope

This project is an evidence-ranking research tool. It does not bypass Instagram access controls, identify private account owners, or prove fraud or image provenance.

## Secrets and private data

Store API keys and deployment credentials in environment variables or the hosting provider's secret manager. Never commit `.env`, wallet credentials, private datasets, user uploads, or raw investigative reports. The repository `.gitignore` excludes common local secret and runtime paths.

The public model and synthetic training data are not secret. Removing Python files from a public repository does not hide source code; use a private repository and a private build/deployment pipeline when source confidentiality is required.

Production deployments should set `ENVIRONMENT=production`,
`REQUIRE_API_KEY=true`, and store `API_KEYS` in the hosting provider's secret
manager. Do not treat `VITE_API_KEY` as a confidential credential: Vite embeds
it in browser assets. Use a private frontend or an authenticated gateway when
the client must not expose a shared browser token.

## Online research safety

Only analyze public URLs that the provider makes available without login. Keep requests bounded, respect provider terms, and review search results manually. Wallet explorer links are leads, not identity attribution.

## Reporting a vulnerability

Do not publish credentials or exploitable details in a public issue. Contact the repository owner privately through GitHub with reproduction steps, impact, and a proposed mitigation.


================================================
FILE: .env.example
================================================
# Runtime configuration
HOST=0.0.0.0
PORT=8000
PYTHON_BIN=python

# API browser access. Use comma-separated exact origins; do not use "*".
CORS_ORIG
