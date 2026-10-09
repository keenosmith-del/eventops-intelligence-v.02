# Architecture decisions

## ADR-001 - One coherent API and workspace

**Accepted.** React routes expose two AI capabilities over a shared FastAPI/domain/database layer. This avoids disconnected demos and makes session, run, evidence and export behavior consistent. The backend owns credentials and business rules.

## ADR-002 - Gemini through the official SDK

**Accepted.** Use the Google Gen AI SDK for document/query embeddings, schema-constrained generation/extraction and explicit function-call planning. Structured response schemas and deterministic validation define service boundaries. Unconfigured live services fail explicitly; fixtures are a separately labeled mode.

## ADR-003 - Exact vector retrieval for a small corpus

**Accepted.** Persist 768-dimensional semantic embeddings in PostgreSQL JSON arrays, rank with cosine similarity in the service and preserve event/record metadata. Thirteen structured records do not justify pgvector operational complexity. This trades scaling efficiency for clarity; move similarity/ranking to pgvector when measured size/latency requires it.

## ADR-004 - PostgreSQL owns durable state

**Accepted.** Sessions, messages, metadata, runs, tool events, verifications and LangGraph checkpoints survive process restarts. SQLite is exclusively a fixture test option. Schema version 1 is reproducibly initialized with SQLAlchemy and checkpoint setup. Future column changes require versioned migrations.

## ADR-005 - LangGraph and n8n have distinct ownership

**Accepted.** LangGraph owns high-level plans, conditional source coordination, extraction, verification and review. n8n exports provide read-only integration operations through protected webhooks. Direct adapters provide the same business interface. Do not duplicate high-level decision logic in n8n.

## ADR-006 - Deterministic authority and human review

**Accepted.** Directory is authoritative for identity/activity/eligibility; registration and invitations provide distinct evidence. Duplicate, incomplete or conflicting records are excluded from verified export. Staff notes create an audit trail; corrections must be evidenced and rerun. The model cannot override business status.

## ADR-007 - Durable queue, leases and checkpoints

**Accepted.** API commits a queued run; a worker claims with PostgreSQL locks, renews a 90-second lease and executes persistent LangGraph transitions. Recovery resumes pending checkpoints. Read-only repeated reads are safe; event history is at-least-once rather than fabricated exactly-once behavior. A sleeping host may pause progress without losing state.

## ADR-008 - Minimal session, separate Google OAuth

**Accepted.** Application access uses a shared backend-validated demo session with opaque HTTP-only cookies. Google access uses separate read-only OAuth consent and encrypted tokens. Credentials never enter frontend code. This satisfies the assessment without an elaborate identity platform; public production beyond the assessment needs stronger account/abuse controls.

## Audit maintenance and limits

This documentation explains component responsibilities, interfaces and architectural decisions; it communicates design intent to implementation/reviewers rather than executing integrations. Validate claims against `backend/app/README.md`, the complete test suite and PostgreSQL verification scripts. The new `usage_counters` table stores atomic durable limits; `scripts/export_schema.py` reproduces the application DDL. The version-1 additive initializer is not a changed-column migration system. Read `docs/submission/compliance-matrix.md` and the deployment policy for current live/deployment blockers; diagrams and decisions cannot establish provider billing or live quality.

## ADR-009 - Deny external spending until unbilled access is established

**Accepted.** R0 is an operating requirement. Fixture mode is the safe default; provider-specific operator attestations plus a global switch are mandatory before live attempts. Persistent atomic daily/operation budgets bound retries and recovered runs; they count attempts rather than currency and cannot make a paid account free. Fixed model/endpoint allowlists, no paid fallback, explicit Developer API and disabled SDK retries keep provider behaviour constrained. Account eligibility or missing durable free hosting remains a documented blocker, with local operation as the safe alternative.
