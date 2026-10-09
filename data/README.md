# Synthetic data

All names, contacts and organizations are fictional. Email addresses use `example.org`.

## Structured knowledge

| File | Schema | Indexed |
|---|---|---|
| `structured/events.json` | Event ID, name, schedule, venue, capacity, deadline | Yes |
| `structured/policies.json` | Record ID, optional event ID, rule and authority | Yes |
| `structured/directory.json` | Participant ID, identity, organization, activity, eligible events | Yes |
| `structured/organizations.json` | Organization catalog | No; supplemental reference |
| `structured/evaluation.json` | Retrieval/answer evaluation cases | No; test specification |

Each indexed document is a JSON array validated by Pydantic; one complete record becomes one chunk. Exact record IDs and source file paths persist with embeddings. No generated overlap is needed for these small structured records.

## Fixtures and expected outcomes

`fixtures/calendar.json` contains calendar-like invitation data; `fixtures/emails.json` includes registration body text plus fixture-only extraction labels. These labels are not used for live extraction. `fixtures/expected.json` records the expected deterministic statuses.

EVT-101:

| Participant | Expected status | Reason |
|---|---|---|
| Amara Dlamini | verified | Consistent active directory, invitation and registration |
| Ben Jacobs | review_required | Duplicate registration messages |
| Cara / Carla Naidoo | review_required | Submitted name conflicts with authoritative name |
| Daniel Mokoena | review_required | Inactive directory contact |
| Elena Petersen | review_required | Conflicting submitted organization |
| Gina Smith | review_required | Missing email, participant ID, organization and invitation |
| Hugo Botha | unverified | No authoritative directory match or invitation |

EVT-102 and EVT-103 each have three clean verified participants. Unavailable information is exercised by tests that fail Calendar, Gmail or directory operations; the system records failures rather than fabricating empty successful sources.

`python3 scripts/seed_data.py` reproduces fixture data. After deliberately changing directory records, synchronize `frontend/public/reference/directory.json` and re-ingest knowledge. For a real tool demonstration create dedicated Google events whose summary contains the exact event ID; use the fixture email bodies as fictional registration messages in the test mailbox. Fixture IDs do not equal Google API-assigned IDs; live evidence retains the real IDs.

## Authority

The published directory owns participant identity, organization, active status and event eligibility. Registration correspondence owns submitted registration fields; Calendar owns invitation evidence. Neither source silently replaces another. A mismatch requires review. RAG's repository knowledge snapshot and the agent's live HTTP directory can diverge if the directory is updated without re-ingestion; track both source versions during a demonstration.

## Domain audit and additional adversarial cases

Before ingestion, `backend/app/rag.py:parse_documents` validates unique event/participant/email identities, event references from policies and directory records, organizations, timezone-aware deadlines and event schedules. These authoritative records must be coherent. Registration evidence is deliberately allowed to contradict them; validation must preserve the discrepancy for verification.

`fixtures/email-edge-cases.json` specifies three additional EVT-102 mutations without changing the seven-row EVT-101 baseline: a valid-format typo, a malformed address, and use of another participant's email. All require review, preserve the submitted address and original source, and cannot enter verified CSV. `test_wrong_and_malformed_emails_cannot_verify` checks each expected status/reason. Other edge cases are covered by `fixtures/expected.json` and `test_verification.py`, including missing directory/source tests.

Run `backend/.venv/bin/python -m pytest backend/tests/test_rag.py backend/tests/test_verification.py -q`. Fixture labels test extraction contracts, not Gemini extraction quality. Local records do not prove consent, receipt of live registrations, or freshness of a published directory.
