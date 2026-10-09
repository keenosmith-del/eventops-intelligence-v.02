# Reproduction and verification scripts

Scripts communicate with application modules, local PostgreSQL, the authenticated API, or static workflow files. Run from repository root using `backend/.venv/bin/python` unless the script needs the separate ReportLab environment.

| Script | Responsibility | Test/limit |
|---|---|---|
| `seed_data.py` | Reproduce authoritative synthetic records and normal fixtures | Review changes against deterministic expected outcomes; additional email cases are separate |
| `init_db.py`, `export_schema.py` | Initialize additive application schema and export PostgreSQL DDL | Does not migrate changed columns or initialize remote billing/resources |
| `ingest.py` | Use the real structure-aware ingestion pipeline | Fixture uses labelled vectors; live invokes bounded Gemini calls |
| `build_n8n_workflows.py`, `check_n8n.py` | Reproduce inactive guarded exports; check auth/wiring/timeouts/retries | Import compatibility and credentialed execution require separate checks |
| `smoke.py` | Authenticated fixture API journey through actual PostgreSQL/worker | Requires running fixture API; does not establish external integration success |
| `check_restart.py` | Compare sessions, metadata, conversation, run/results/events and counter before/after process restart | Private cookie file mode 0600 removed afterward; wait two seconds after another login because login throttling is intentional |
| `check_checkpoint.py` | Reconstruct PostgreSQL saver and resume unfinished graph | Fixture sources; proves durable graph continuation |
| `check_budget.py` | Atomic PostgreSQL quota contention and connection reconstruction | Simulated approval/clock in isolated audit namespace; zero provider calls; never validates a real account's free tier |
| `live_preflight.py` | Explicitly report missing live configuration/policy confirmations | No network; exit 2 means blocked, not skipped/passed |
| `evaluate_rag.py` | Genuine Gemini retrieval/generation cases with recorded results | Credentials/policy/index required; default four cases to fit daily cap, remaining cases scheduled next day; manual entailment review still required |
| `build_reports.py` | Render initial submission Markdown reports to PDF | Requires ReportLab and PDF visual QA; PDFs are initial implementation snapshots, current audit is in compliance matrix |

For operational checks follow `docs/testing/results.md`. For actual external calls follow the zero-cost policy first, then `docs/testing/live-checks.md`. None of these scripts provisions cloud infrastructure or enables billing.
