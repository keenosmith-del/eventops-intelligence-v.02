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
