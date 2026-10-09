# Assessment compliance matrix

Audit: 10 October 2026. Architecture and Git history preserved. Current local checks: **55 backend tests, nine frontend tests, production frontend build passed**; actual local PostgreSQL restart/checkpoint/budget tests passed; three guarded workflows imported into local n8n 2.42.6. **No Gemini, Google OAuth/Calendar/Gmail, credentialed n8n execution, public HTTP directory or public deployment is claimed verified.**

Status legend: **Local** = implemented and exercised without paid/external services; **Fixture** = implemented provider path but exercised only with fixtures/mocks; **Real local** = actual PostgreSQL/n8n runtime verified, not provider execution; **Credentials pending** = genuine API access/quality unverified; **Deployment pending** = public host/storage/account not verified; **Incomplete** = required assessment evidence or functionality not yet delivered. A requirement may have several statuses; implementation readiness is not end-to-end assessment completion.

Paths below are repository-relative. Tests under `backend/tests/`; provider evidence follows `docs/testing/live-checks.md`. See [test results](../testing/results.md), [zero-cost policy](../deployment/README.md), and [application module interfaces](../../backend/app/README.md).

## Part 1 — RAG

| Requirement | Source files | Relevant verification | Status | Credentials/access and remaining limits |
|---|---|---|---|---|
| At least three structured documents | `data/structured/{events,policies,directory}.json`, `backend/app/schemas.py` | `test_rag.py`; PostgreSQL smoke: three documents/13 records | Local | None; organization catalog is supplemental |
| Real structured ingestion | `backend/app/rag.py:parse_documents,ingest` | Schema/domain tests, authenticated smoke | Local; genuine model ingestion credentials pending | Gemini required for live vectors; atomic replacement/checksum tested |
| Structure-aware chunks | `rag.py`, `db.py:Chunk` | Record-count/source tests | Local | Whole logical record per chunk; small curated corpus |
| Semantic embeddings | `ai.py:embed` | Shape/failure/policy tests; fixture vectors | Fixture; credentials pending | Exact configured model access and unbilled pricing required; fixture vectors are not semantic evidence |
| Vector retrieval | `rag.py:cosine,retrieve` | Ranking/filter/dimension/non-finite tests | Local algorithm; semantic quality credentials pending | Exact scan of JSON vectors; no ANN/pgvector scaling |
| Query transformation/prompt control | `ai.py:intent,structured` | Explicit event/context tests | Fixture; credentials pending | Live Gemini contextual rewriting not executed; bounded history/input |
| Grounded Gemini generation | `ai.py:answer`, `rag.py:ask` | Citation/support contracts | Fixture; credentials pending | No live answer/entailment evaluation; citation membership alone is insufficient |
| Source traceability | `db.py:Document,Chunk,Message`, `rag.py` | Source-ID tests and actual saved API evidence | Local | Traceability implemented; manual factual entailment still required live |
| Abstention with missing evidence | `ai.py:answer`, `rag.py:ask` | Unsupported query and no-model-on-empty-evidence tests | Local deterministic; model quality credentials pending | No-evidence path does not call generator; irrelevant nonempty evidence still needs live quality evaluation |
| Persistent conversational context | `db.py:Conversation,Message`, `rag.py`, frontend | Context/ownership tests; actual backend restart | Real local | Eight prior messages, 4,000 chars each; shared operator |
| Reproducible ingestion | `rag.py`, `scripts/seed_data.py,ingest.py` | Idempotent checksum and invalid-input tests | Local | Checksum includes mode/model; mode/model changes require re-ingestion; initial schema version only |
| Representative RAG evaluation | `data/structured/evaluation.json`, `scripts/evaluate_rag.py` | Seven factual/multi-record/ambiguous/unsupported/exact-ID/conflict/activity cases; staged evaluator | Local specification; live evaluation incomplete | Gemini access and manual entailment grading required; all selected cases/results must be retained |
| Web deployment readiness | `frontend/vercel.json`, `render.yaml`, Dockerfile/config | Build and production config tests | Local readiness; deployment pending; live submission incomplete | Hosting authorization, actual unbilled tiers and durable PostgreSQL missing; cross-site cookies/cold starts unverified |

## Part 2 — AI agent

| Requirement | Source files | Relevant verification | Status | Credentials/access and remaining limits |
|---|---|---|---|---|
| LangGraph orchestration | `backend/app/agent.py` | `test_agent.py`; real Postgres checkpoint continuation | Real local | Durable checkpoints verified; sleeping cloud hosts pause workers |
| Meaningful decisions | `ai.py:plan`, conditional graph in `agent.py` | Tool allowlist/partial-source/conditional-review tests | Fixture; credentials pending | Gemini function-call selection implemented; fixture plan fixed and labelled |
| n8n workflows | `automations/n8n/*.json`, generator | Static validation plus actual import into 2.42.6 | Real local import; credentialed execution pending | Header/OAuth credentials and fixed host required; inactive explicit deny defaults; PG16 compatibility warning |
| Google Calendar | `integrations.py`, Calendar workflow | Adapter mocks, fixture graph | Fixture; credentials pending | Dedicated read-only OAuth account, current unbilled quota proof; 100 events, no pagination |
| Gmail | `integrations.py`, Gmail workflow | Failure/fan-out-limit tests, fixture graph | Fixture; credentials pending | Same consent/quota proof; direct 30 / n8n 20 message cap |
| Actual web HTTP integration | `integrations.py:request_json,Tools`, web workflow | HTTP mocks/allowlist/JSON failures; static directory equality | Fixture; deployment pending; required live evidence incomplete | Real reachable HTTPS directory and unbilled host missing; repository read is not HTTP verification |
| Structured extraction | `ai.py:extract`, `schemas.py:Extraction` | Agent/schema/source contract tests | Fixture; credentials pending | Genuine email extraction not executed; exact field occurrence checks reject invented fields |
| Normalization | `verify.py:normalized,email_key,name_key` | Unicode/whitespace/case/source-preservation tests | Local | Originals retained; no silent repair |
| Deduplication | `verify.py` | Expected duplicate registration/invitation tests | Local | Groups retain evidence and mark review; no automatic loss of duplicate messages |
| Deterministic verification | `verify.py`, expected fixtures | All status/identity/org/activity/event/incorrect-email tests | Local | Authority snapshot must be unique/current; source contradictions block verification |
| Evidence references | `verify.py`, `db.py:Verification,Execution` | Original IDs/values tests and actual API results | Local | Live IDs await actual Google/HTTP runs |
| Error handling | `ai.py`, `integrations.py`, `agent.py`, `main.py`, `costs.py` | Timeout/retry/invalid-output/source/denial/exhaustion tests | Local mocks; real local queue/store | Genuine quota/consent/network failure behaviour still to exercise; no successful fallback manufactured |
| Human review | Conditional graph and `main.py` review API, frontend | Review-required branch and smoke note | Local | Reviewer notes and unresolved rows implemented; no formal approval/resume state machine or identity correction UI |
| CSV export | `main.py` export route and frontend API | Auth/verified-only/formula-safety tests and actual smoke | Local | Only verified rows; unresolved rows excluded |
| Persistent execution history | `db.py:Run,Execution,Verification`, graph saver | API persistence, restart and pending saver tests | Real local | At-least-once reads/events on crash; production retention pending |

## Cross-cutting requirements

| Requirement | Source/evidence | Verification/status | Access/remaining limitation |
|---|---|---|---|
| Coherent domain relationships | `rag.py:parse_documents`, authoritative event/policy/directory/organization data | Local: unique IDs, dates/timezones, eligible events and organizations; public snapshot equality | Registration contradictions intentionally preserved |
| Deliberate edge cases | `fixtures/expected.json,email-edge-cases.json`, `verify.py` | Local: duplicates, missing fields, typo/malformed/another identity's email, conflicting names/org, inactive and absent directory | Live mailbox/calendar still must reproduce fictional evidence |
| Durable metadata/context/runs/results/events | `restart-check.json`, `checkpoint-check.json`, `budget-check.json` | Real local: three document checksums, two conversation messages, run, seven results, 13 events, session and counter survived restart; unfinished graph resumed | Production database retention and remote restart not executed |
| Production avoids ephemeral state | PostgreSQL models/checkpointer, `render.yaml`, config tests | Local production validation passed; deployment pending | No production account/storage available; n8n needs persistent DB/config and stable key |
| R0 cost safety | `costs.py`, config/AI/tool/workflow guards, deployment policy | Local: atomic caps/deny defaults, bounded retries/input/fan-out, server-side credentials; no billing/resources enabled | Provider flags attest account state rather than prove it; public strict R0 unconfirmed |
| Unified frontend/user journey | `frontend/src/main.tsx,api.ts,styles.css`, six views | Nine frontend tests and production build passed; earlier real fixture browser journey recorded | Actual live browser/provider/deployment journey pending; system-font audit change verified by regression/build |
| API/contracts/security | `main.py`, `schemas.py`, encrypted credentials, Origin/ownership checks | API tests and actual smoke; OpenAPI exposed; server-only secrets and read-only consent boundaries | Shared assessment operator; public multi-tenant/abuse protection outside scope |
| Architecture diagrams/ADRs | `docs/architecture/README.md`, `docs/decisions/README.md` | Five Mermaid flows and recorded decisions implemented | Design documentation cannot prove live operation |
| Reports and 20–30 minute walkthrough | `docs/submission/*`, `output/pdf/*` | Initial Markdown/PDF reports and 25-minute walkthrough prepared | Present with current compliance status; live demonstration evidence still incomplete |
| Documentation per module | Root/backend/app/tests/frontend/data/automations/scripts/docs READMEs | Updated responsibilities/interfaces/tests/limits | Initial PDF reports remain historical implementation snapshots; refresh for final submission only after live evidence |
| Complete local tests | `docs/testing/results.md` plus executable scripts | 55 backend + nine frontend passed; build/static/import/Postgres checks passed | Live preflight **blocked**, not skipped/passed; actual API/model/deployment tests not executed |

## Submission decision

The implementation and deterministic local demonstration are ready for review. **The original assessment is not submission-complete:** genuine semantic RAG/model decisions/extraction, Calendar/Gmail and web HTTP reads, credentialed n8n execution, public deployment and actual-account R0 evidence are incomplete verification requirements. No implementation test substitutes for them.

Follow the exact nine-step live/deployment sequence in [operating policy](../deployment/README.md#exact-steps-for-genuine-live-verification). Required access: unbilled Gemini key/model eligibility and pricing proof; dedicated Google test account/OAuth/consent/current quota proof; stable encryption key; confirmed-unbilled HTTPS directory; n8n OAuth/shared secret and durable host; Vercel/Render account authorization/plan/payment-state evidence; durable confirmed-unbilled PostgreSQL. Do not upgrade or enable billing to unblock any requirement.
