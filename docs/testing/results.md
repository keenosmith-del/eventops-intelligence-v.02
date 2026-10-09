# Validation record

Recorded on 10 October 2026 (Africa/Johannesburg). Source files and executable check scripts are included in the repository; no successful live integrations are inferred from fixtures.

| Check | Established result |
|---|---|
| Backend pytest suite | 32 passed |
| Frontend Vitest suite | 9 passed |
| TypeScript + Vite production build | Passed |
| npm dependency installation/audit | Updated Vitest to 5.0.3; installation reported zero known vulnerabilities |
| Workflow static checks | Three exported JSON workflows passed wiring/header-auth checks |
| Docker PostgreSQL | Running and healthy; application data ingested |
| Local n8n | Stable 2.42.6 running; all three workflows reimported successfully |
| Real local API + PostgreSQL smoke | Passed sign-in, ingestion, RAG contract, saved history, idempotency, worker, verification, CSV and review note |
| PostgreSQL pending checkpoint | Recreated saver, resumed unfinished source collection, completed EVT-103 with three verified records |
| Backend restart | Session, conversation, run and seven verification records survived |
| Browser dashboard | Rendered actual counts: three documents, thirteen records, persisted run/review history |
| Browser frontend agent request | Started EVT-102 through the actual form; persisted run completed with three verified rows |
| Browser responsive results | Desktop and 390px layouts inspected; actual screenshots saved |
| Browser knowledge view | Restored saved messages and inspectable original source records |
| Live Gemini semantic evaluation | Not executed; key/account quota unavailable |
| Google Calendar/Gmail OAuth calls | Not executed; dedicated account authorization unavailable |
| Credentialed n8n source execution | Not executed; OAuth/webhook credentials unavailable |
| Public deployment and HTTP directory | Not executed; hosting access unavailable |

The full API smoke and restart evidence is stored in `postgres-smoke.json`, `restart-check.json` and `checkpoint-check.json`. Real fixture-browser screenshots are in `screenshots/`; their visible fixture badges are intentional. All operational outcomes shown came from actual test runs, not hardcoded execution history.

Default ports 5050 and 5173 were already occupied. Verification used this project's isolated ports 5051 and 5174; unrelated services were left untouched. The normal startup defaults remain unchanged.

Browser testing found unnecessary GET request preflights and a localhost private-network CORS issue. The frontend now sets JSON Content-Type only when sending a body, and local private-network preflight is permitted only for an explicitly configured localhost frontend. Production origins retain the stricter setting. The authenticated dashboard then loaded successfully.

The n8n 2 import initially required explicit workflow version IDs. The export generator now includes deterministic workflow/version identifiers; corrected exports imported successfully. The CLI printed missing-webhook cleanup warnings for new workflow IDs, followed by successful import. This is import compatibility evidence, not execution evidence.

## Reproduction

```sh
backend/.venv/bin/python -m pytest backend/tests -q
python3 scripts/check_n8n.py
cd frontend
npm test
npm run build
```

With local application services running in fixture mode, run `scripts/smoke.py` using `backend/.venv/bin/python`. For alternate verification ports set `SMOKE_API_URL` and `FRONTEND_ORIGIN` consistently. Restart verification uses `scripts/check_restart.py before`, a controlled backend restart, then `scripts/check_restart.py after`; it saves a temporary private cookie file with restrictive permissions and removes it after checking.

Tests use model/tool doubles and isolated temporary SQLite databases. The smoke test uses the real PostgreSQL application and checkpoint storage. A real Gemini evaluation and external tool demonstration must follow `live-checks.md` before the assessment's mandatory live requirements are claimed complete.

## Hardening audit verification — 10 October 2026

This section supersedes the earlier implementation counts. **55 backend tests and nine frontend tests passed**, including all existing cases. TypeScript/Vite production build passed after removing external fonts. Focused Ruff checks (`E4,E7,E9,F`) and whitespace validation passed. No claim is made that every optional lint rule is enforced.

| Additional check | Observed result |
|---|---|
| Default external denial | Fixture with a configured key never creates an SDK client; HTTP denied before attempt |
| Atomic persisted limits | 12 concurrent PostgreSQL reservations accepted exactly three at cap three; counter survived connection reconstruction; zero provider calls |
| Retry/failure budgets | Retried mock model failures consume durable units and stop at operation cap; SDK retries disabled |
| Fan-out/replay controls | Oversized Gmail ID list rejected before message reads; n8n workflow POST never replayed |
| Domain/source checks | Authoritative cross-references/dates/organizations validated; published directory equals authoritative snapshot; wrong/malformed/another identity's email cannot verify |
| Local vs production config | Production rejects SQLite, insecure cookies, HTTP frontend and missing remote DB SSL; valid local/production settings tested separately |
| Real local API smoke | Updated API on port 5052 passed the full journey, seven EVT-101 rows, one verified |
| Actual process restart | Three document checksums, conversation, run, seven results, 13 events, session and usage counter survived |
| Pending graph checkpoint | Saver reconstruction resumed unfinished EVT-103 and completed three verified rows |
| Updated n8n imports | All three inactive externally blocked exports imported successfully into actual local 2.42.6 |
| Live preflight | Executed; exit 2, explicitly blocked by missing configuration/account confirmations; zero external calls |
| Genuine provider/deployment acceptance | Not executed: credentials/account/hosting evidence unavailable; see compliance matrix |

n8n CLI reports that PostgreSQL 16 receives compatibility support only and recommends 17 or later; imports succeeded. A planned backup/restore upgrade remains a maintenance recommendation, not an automatic image change. A first restart-baseline login immediately after smoke received the expected two-second throttle; rerun after the window succeeded. Initial API startup inside the restricted network sandbox could not access local PostgreSQL; the approved local-network run then passed. Neither transient check issue is represented as a successful live integration.

Current evidence: `postgres-smoke.json`, `restart-check.json`, `checkpoint-check.json`, `budget-check.json`, `live-preflight.json`. Earlier browser screenshots remain fixture evidence from the initial implementation; the hardening audit did not repeat browser interaction or visual inspection after the system-font change. Frontend regression tests and build were repeated. Production restart/storage and cross-site browser behaviour still await deployment.

Additional reproduction (local fixture PostgreSQL only):

```sh
backend/.venv/bin/python scripts/check_budget.py
backend/.venv/bin/python scripts/check_checkpoint.py
SMOKE_API_URL=http://localhost:5052 FRONTEND_ORIGIN=http://localhost:5174 backend/.venv/bin/python scripts/smoke.py
# Wait two seconds after smoke login before the next sign-in.
SMOKE_API_URL=http://localhost:5052 FRONTEND_ORIGIN=http://localhost:5174 backend/.venv/bin/python scripts/check_restart.py before
# Stop/restart this project's isolated API with the same database/settings.
SMOKE_API_URL=http://localhost:5052 FRONTEND_ORIGIN=http://localhost:5174 backend/.venv/bin/python scripts/check_restart.py after
backend/.venv/bin/python scripts/live_preflight.py  # exit 2 is current explicit blocked status
```

Live evaluation is separately gated and runs at most four cases per invocation by default. Prior completed case IDs are retained; remaining cases can be executed in a later UTC quota window without raising caps. A partial or failed evaluation is not complete; manually grade factual grounding before marking the assessment verified.
