# Database boundary

Version 2.0 defines persistence interfaces only. No concrete database engine
is enabled yet. Future PostgreSQL, SQLite, or another adapter must implement
the protocols under `database/interfaces/` without coupling FastAPI routes to
the selected storage technology.
