# Security Policy

## Scope

This policy covers the Streamlit application, its Python SDK, the GitHub Actions
workflows, the optional n8n workflow export, and the packaged model artifacts in
this repository.

The application is an evidence-ranking tool. It is not an identity-verification,
fraud-determination, or access-control system.

## Supported versions

Only the latest commit on `main` is supported. This project does not currently
publish versioned security fixes.

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability. Report it
privately through GitHub's **Report a vulnerability** option on the repository's
Security tab. Include:

- affected commit, file, or workflow;
- deployment type and relevant configuration;
- reproduction steps or a minimal proof of concept;
- security impact and any required permissions or user interaction;
- logs or screenshots with credentials, tokens, personal data, and private
  profile information removed.

If private reporting is unavailable, contact the repository owner through a
private GitHub channel and request a security contact. Do not include secrets in
the report.

We will acknowledge a valid report when practical, investigate the impact, and
coordinate disclosure after a fix or mitigation is available. There is no bug
bounty or guaranteed response time.

## Deployment guidance

- Run Streamlit behind HTTPS and an authenticated reverse proxy when the app is
  not strictly local.
- Do not expose the n8n webhook without authentication and rate limiting.
- Store `GOOGLE_API_KEY`, `GOOGLE_CSE_ID`, `BING_SEARCH_KEY`, and `GITHUB_TOKEN`
  only in the deployment secret manager or environment; never commit them.
- Treat uploaded JSON, captions, URLs, and images as untrusted input.
- Restrict outbound network access where possible and monitor request volume.
- Keep Python dependencies, GitHub Actions, n8n, and model artifacts updated from
  trusted sources.
- Do not use the detector's heuristic output as the sole basis for decisions
  affecting a person.

## Known limitations

The post-analysis feature makes outbound requests to Instagram metadata, search
providers, and image URLs. URL validation restricts the submitted post URL to
Instagram, but deployments should still use egress filtering because public
metadata and redirects are external input. The application does not claim that
its search, wallet, image, or model signals prove fraud or identify a person.