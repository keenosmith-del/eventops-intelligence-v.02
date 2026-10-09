# Local development

Use root, backend and frontend READMEs for commands. Docker Desktop must be running. The Compose PostgreSQL/n8n services bind to loopback and persist in named volumes. PostgreSQL port 5432; n8n 5678; backend 5050; Vite 5173. No other project is required.

## Common problems

- **Port occupied:** do not terminate an unrelated application. Stop your own older process or use temporary ports with matching API/origin settings. To reproduce the verification session: `FRONTEND_ORIGIN=http://localhost:5174 .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 5051` in backend, then `VITE_API_URL=http://localhost:5051 npm run dev -- --port 5174 --strictPort` in frontend. These overrides do not change the required defaults.
- **401 after login:** use `localhost` consistently, check SameSite/Secure flags, and avoid cross-site HTTP.
- **403 mutation:** browser Origin must equal `FRONTEND_ORIGIN` exactly. Command-line clients must send that Origin explicitly.
- **Database unavailable:** `docker compose ps`; check credentials and port binding. Never run `docker compose down -v` unless deliberately destroying local data.
- **Live embeddings fail:** verify key, free model availability and quotas. Do not switch silently to fixtures. Model IDs are configurable; re-ingest after embedding model changes.
- **Wrong index mode:** switching MODE requires re-ingestion. Mode and embedding model are part of the ingestion checksum.
- **No Google data:** reconnect the dedicated account, confirm consent, event ID in Calendar summary, and event-specific subject in Gmail.
- **n8n 401/404:** assign Header Auth and activate/publish production webhooks. Test paths need n8n listening mode.
- **Backend sleeps/restarts:** saved sessions/conversations survive, and expired worker leases resume unfinished graph transitions. Frontend polling wakes an idle backend during a viewed execution.

Local fixture tests use isolated temporary SQLite databases, not the operational PostgreSQL database. Never point destructive unit-test reset logic at deployed storage.
