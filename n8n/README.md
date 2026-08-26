# n8n workflow

`github-quality-dispatch.json` exposes a webhook that dispatches the repository's
`python-quality.yml` workflow through the GitHub API.

## Setup

1. Import the JSON file into n8n.
2. Set the n8n environment variable `GITHUB_TOKEN` to a GitHub token with
   Actions: write permission for `Root-Tester/instgram_fake_account_detector`.
3. Protect the webhook with n8n header authentication or an authenticated
   reverse proxy before activating it. The exported webhook is inactive by
   default.
4. Activate the workflow and call its production webhook URL with `POST`.

The workflow runs the quality checks on the `main` branch. SLSA provenance remains
available through the separate GitHub workflow's manual trigger or release trigger.