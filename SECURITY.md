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