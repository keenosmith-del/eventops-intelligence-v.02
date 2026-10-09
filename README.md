# EventOps Intelligence

An event operations workspace combining evidence-grounded knowledge retrieval with a bounded attendee-verification agent. React/Vite/TypeScript frontend; Python 3.12/FastAPI backend; Gemini embeddings, generation, structured extraction and function calling; LangGraph orchestration; PostgreSQL persistence; optional n8n integration transport.

## Delivery status

The implementation supports live services, but credentials and hosting authorization must be supplied before the assessment's live RAG, real Google and public deployment requirements can be demonstrated. No deployment URL or live evaluation is claimed. `MODE=fixture` runs an explicitly labeled local demonstration with synthetic records and deterministic model doubles. It does **not** establish semantic retrieval quality or successful external integrations.

The [verification report](docs/testing/results.md) records executed checks. Read [deployment](docs/deployment/README.md) for exact account actions and [live checks](docs/testing/live-checks.md) before presenting the assessment as complete.

## Quick start on macOS

Prerequisites: Git, Python 3.12, Node 22+ and Docker Desktop running. All commands below start from this repository; do not use another project.

```sh
cd /Users/keenosmith/Programming/Projects/inference-group/eventops-intelligence-v.02
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.lock
```

Edit root `.env` to set a random `N8N_ENCRYPTION_KEY`. Edit `backend/.env` to set a strong `DEMO_PASSWORD`. For a credential-free demonstration set `MODE=fixture`. For live operation set `MODE=live` and follow the Google/Gemini setup in the backend README. Do not overwrite existing configured environment files.

```sh
docker compose up -d
backend/.venv/bin/python scripts/init_db.py
backend/.venv/bin/python scripts/ingest.py
cd backend
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 5050
```

In a separate terminal:

```sh
cd /Users/keenosmith/Programming/Projects/inference-group/eventops-intelligence-v.02/frontend
npm ci
npm run dev
```

Open http://localhost:5173, sign in as `operator` using the backend-configured password. Use `localhost` consistently across browser/API configuration; mixing `127.0.0.1` with `localhost` can prevent cookie delivery. FastAPI OpenAPI is at http://localhost:5050/docs. n8n is at http://localhost:5678.

During implementation, ignored local environment files were provisioned for fixture mode. The random demo password is in `backend/.env`; it is never included in source or frontend bundles.

## Demonstration

1. Ingest the three structured knowledge documents on Overview.
2. Ask a question about EVT-101; expand original record evidence.
3. Refresh to verify saved conversation continuity.
4. Request a verified attendee list for EVT-101 in Agent Workspace.
5. Inspect planning, selected tools, source counts, extraction, verification and review transitions.
6. Review the discrepancies; save a human note.
7. Export verified-only CSV. EVT-101 exports Amara; EVT-102 and EVT-103 have three clean registrations each in fixture mode.
8. Inspect persisted execution history after a backend restart.

## Checks

```sh
backend/.venv/bin/python -m pytest backend/tests -q
python3 scripts/check_n8n.py
cd frontend
npm test
npm run build
```

[`scripts/smoke.py`](scripts/smoke.py) verifies the complete API journey against running PostgreSQL services. Live evaluation: `backend/.venv/bin/python scripts/evaluate_rag.py` after switching to live mode and ingesting genuine Gemini embeddings.

## Repository guide

| Directory | Responsibility |
|---|---|
| `frontend/` | Six responsive views, authenticated fetch, evidence, polling and export |
| `backend/app/` | API, database, RAG, Gemini, integrations, graph and verification |
| `backend/tests/` | Repeatable contract, failure, retrieval and checkpoint tests |
| `data/` | Three indexed documents, organization data, fixtures and evaluation cases |
| `automations/n8n/` | Authenticated Calendar/Gmail/HTTP workflow exports |
| `docs/` | Architecture, decisions, security, deployment, validation and submission |
| `scripts/` | Initialization, reproducible fixtures, workflow export and checks |

## Operational boundaries

Read-only integrations never send messages or modify calendars. One shared demo operator is intentionally supported; this is not a multi-tenant identity system. Knowledge is curated from repository data, not arbitrary uploads. Directory URL is server configured, not chosen by the model. Durable deployment requires managed PostgreSQL and persistent n8n storage. No paid infrastructure is provisioned by this repository.
