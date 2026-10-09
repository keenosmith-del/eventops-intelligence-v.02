# Backend

Python 3.12 / FastAPI, SQLAlchemy with psycopg, official Google Gen AI SDK and LangGraph. Run from `backend/`: `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 5050`. Configuration loads `backend/.env` independently of the working directory.

## Configuration

Copy `.env.example` to `.env` only if no file exists. Set `DEMO_PASSWORD`; startup refuses an empty password. PostgreSQL is required in live mode. SQLite is permitted only for isolated fixture tests. The default demonstration is not automatically substituted when a live dependency fails.

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg://...`; use managed provider SSL parameters in production |
| `MODE` | `live` or explicitly selected `fixture` |
| `DEMO_USERNAME`, `DEMO_PASSWORD` | Server-only shared operator credentials |
| `FRONTEND_ORIGIN` | Exact allowed origin, no trailing slash |
| `COOKIE_SECURE`, `COOKIE_SAMESITE` | Local `false/lax`; cross-site HTTPS `true/none` |
| `GEMINI_API_KEY` | Gemini Developer API key from an account with free access; no billing enabled |
| `GEMINI_MODEL`, `EMBEDDING_MODEL` | Configurable model IDs; defaults 2.5 Flash / embedding-001 |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Dedicated Google OAuth web application |
| `GOOGLE_REDIRECT_URI` | Exact callback URI registered in Google Cloud |
| `TOKEN_ENCRYPTION_KEY` | Persistent Fernet key; losing it makes saved tokens unreadable |
| `CALENDAR_ID` | Dedicated synthetic calendar identifier; `primary` by default |
| `DIRECTORY_URL` | Operator-controlled HTTPS JSON array |
| `INTEGRATION_TRANSPORT` | `direct` or `n8n` |
| `N8N_BASE_URL`, `N8N_WEBHOOK_SECRET` | Protected production webhook base and shared header key |
| `WORKER_ENABLED` | Enable durable polling worker; disabled workers reject new runs |

Generate the encryption key locally:

```sh
.venv/bin/python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

## Google authorization

1. In a dedicated Google Cloud project, enable Calendar API and Gmail API. Do not enable paid services or billing.
2. Configure OAuth consent for a testing application and add the fictional demonstration mailbox as a test user.
3. Create a web OAuth client with the exact local callback `http://localhost:5050/api/integrations/google/callback`; register the actual HTTPS backend callback for deployment.
4. Set client ID/secret, callback and Fernet key server-side. Restart the backend.
5. Sign in to EventOps, click **Connect Google test account**, select the test account and grant only Calendar events read-only and Gmail read-only access.
6. The backend stores tokens encrypted in PostgreSQL, checks state against the active session and refreshes tokens as needed. Testing-mode authorization may require reconnection when Google expires it.
7. Populate the account with the fictional events and messages from `data/fixtures/`. No account data is published as a directory.

For `n8n` transport, authorize Google separately in n8n and assign those credentials to the exported HTTP API nodes. EventOps's direct OAuth connection is not forwarded to n8n.

## Services

- `rag.py`: schema validation, atomic/idempotent index updates, exact record chunks, vector ranking, intent resolution and citation validation.
- `ai.py`: semantic embeddings, structured answers/extraction, bounded Gemini function-call plans and model boundary checks.
- `integrations.py`: timeouts/retries, refresh tokens, Calendar/Gmail reads, fixed HTTPS directory access and n8n adapter.
- `agent.py`: conditional graph, persistent checkpoints, lease-based queue claims, heartbeat and results persistence.
- `verify.py`: deterministic source hierarchy, missing fields, duplicates, identity and organization conflicts, active status and event eligibility.

## Database initialization

From repository root: `backend/.venv/bin/python scripts/init_db.py`. Application tables use SQLAlchemy `create_all` as reproducible version-1 initialization; this does not migrate changed columns. A PostgreSQL DDL export is at `docs/architecture/schema.sql`. LangGraph's Postgres saver performs its own checkpoint schema setup at startup. Before evolving production schemas, introduce a versioned migration tool and backups.

Worker deployment uses one Uvicorn process by default. PostgreSQL row locks protect claims; leases renew while a graph runs. Checkpoints resume unfinished transitions after lease expiry. Read-only integrations permit safe repeated reads. Execution logs provide at-least-once records; duplicate tool events may occur across crash recovery and are not silently removed.
