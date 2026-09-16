# Version 2.0 architecture

The repository root is the project boundary. The application is intentionally
split into clear ownership areas:

- `backend/` contains the FastAPI application, Python package, backend tests,
  and backend dependency metadata.
- `database/` contains persistence interfaces and schema/migration
  placeholders only; no concrete database is selected yet.
- `frontend/` contains the React/Vite client.
- `shared/` contains stable cross-layer contracts and types.
- `models/` and `data/` contain reviewed artifacts and public/sample data.
- `scripts/` contains training and maintenance tooling.
- `infra/` and `docs/` contain deployment and architecture material.

There is no second repository-name application directory. The
`backend/app/instgram_fake_account_detector` directory is the maintained Python
import package, not a duplicate project root.
