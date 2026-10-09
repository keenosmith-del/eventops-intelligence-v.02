# Backend application modules

These modules implement the authenticated operational API; all durable application state belongs in PostgreSQL. Run `backend/.venv/bin/python -m pytest backend/tests -q` from repository root. Unit tests use isolated SQLite fixture storage; operational PostgreSQL and real provider checks are separate.

| Module | Responsibility and implemented interface | Verification | Limitations |
|---|---|---|---|
| `config.py` | Environment settings; `settings()` validates local/production storage, HTTPS, cookies, model allowlist and hard limits | `test_costs.py` | Operator attestations cannot prove provider billing state |
| `db.py` | SQLAlchemy models, DB sessions, initialization, durable execution logs and usage counters | API/agent tests; restart and budget scripts | Additive `create_all`; no changed-column migration or database-level foreign keys |
| `costs.py` | Deny external calls by default; atomic daily/operation reservations; context propagated to RAG and worker | Concurrency, denial, exhaustion, reconnection tests; `check_budget.py` | Counts attempts, not currency; hosted account changes require re-audit; counters retained |
| `schemas.py` | Strict API, authoritative knowledge, extraction and response contracts | All backend tests | Semantic field correctness still requires source comparison |
| `ai.py` | Official Gemini embeddings, intent, answers, structured extraction and allowed function-call planning | RAG/agent/cost tests; separate `evaluate_rag.py` | Provider execution and semantic quality await credentials; no alternate provider fallback |
| `rag.py` | Validate domain references; atomic checksum ingestion; record chunks; cosine retrieval; grounded response contract; save context | `test_rag.py`; API smoke | Small corpus uses JSON vectors and exact scanning; citation membership does not prove entailment; eight prior messages capped at 4,000 characters each |
| `integrations.py` | Encrypted OAuth tokens, bounded Google reads, fixed directory HTTP, authenticated n8n envelope | `test_integrations.py`; workflow import checks | OAuth/Google/HTTP live execution pending; source pagination is rejected; fixed directory still must be trusted |
| `verify.py` | Normalize, group duplicates, compare every source against active eligible directory identity; retain evidence | `test_verification.py` | No silent correction of identities; uncertain records require review |
| `agent.py` | LangGraph transitions and conditional review; persisted queue claims/leases/checkpoints/results | `test_agent.py`; PostgreSQL checkpoint/restart checks | At-least-once reads/events on crash; human review records notes rather than resuming approval workflow; sleeping hosts pause execution |
| `main.py` | Authentication, ownership/Origin checks, ingestion/query/run/review/export/OAuth routes, startup worker | `test_api.py`; `smoke.py` | Shared assessment operator; cross-site browser cookies require live verification |

Communication is explicit: FastAPI invokes RAG or queues runs; the worker invokes LangGraph; AI and tools apply cost guards before external attempts; deterministic verification never calls a model; SQLAlchemy and the Postgres checkpointer retain state. Provider credentials stay in backend environment/encrypted database, or n8n's encrypted store. No credential is transmitted in frontend settings.
