# Deterministic backend tests

`conftest.py` forces fixture mode and isolated temporary SQLite storage, disables the background worker, and recreates only that temporary schema for each test. Run `backend/.venv/bin/python -m pytest backend/tests -q` from repository root.

API tests exercise auth/ownership/Origin, persistent records and export. RAG tests exercise ingestion, metadata/source IDs, retrieval, context and abstention contracts. Agent tests execute real LangGraph with fixture sources and memory checkpoints. Verification tests assert expected contradictions, deduplication and adversarial emails. Integration tests mock HTTP/model failures; costs tests check atomic contention, persisted limits, provider denial and local/production validation. No test establishes a live provider result. PostgreSQL restart/checkpoint/budget checks live in `scripts/`; credentialed quality/execution tests live in the documented live checklist.
