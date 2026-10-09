# Genuine live integration verification

Run only with dedicated fictional accounts. Set `MODE=live`; never present fixture evidence as live evidence.

## RAG

1. Configure a Gemini key with free quota; inspect `/api/status` for configuration without exposing the key.
2. Re-ingest three documents; confirm ingestion metadata says `mode=live`, the configured Gemini embedding model and 768 dimensions.
3. Ask exact-ID factual, global policy and multi-record questions; expand source IDs and compare every factual assertion with those records.
4. Ask an unsupported weather question and an ambiguous question without conversation context; verify refusal or clarification rather than invented facts.
5. Ask a contextual follow-up, reload the browser and restart the backend; verify history and context persist.
6. Run `scripts/evaluate_rag.py`; inspect retrieval recall, expected answer terms and support classification. The script records generated evidence, not expected successful outputs. Manually grade semantic grounding and ambiguity handling. Do not treat citation membership alone as entailment.

## Direct Calendar/Gmail/HTTP

1. Authorize the dedicated Google account through the app's OAuth flow. Confirm encrypted credential storage and working refresh; decline consent in a second test and confirm a meaningful error.
2. Populate at least three fictional calendar events with exact event IDs and fixture-derived attendee invitations. Store fixture email bodies in the dedicated mailbox with event IDs in their subjects.
3. Publish the fictional directory at the configured HTTPS URL; request it independently and verify schema and records.
4. Start EVT-101 verification. Confirm the planner uses Gemini function calls and history records real source counts and source IDs returned by Google/HTTP.
5. Verify extraction from email bodies uses Gemini structured output, not fixture extraction labels. Compare each field to its original message.
6. Confirm the intended duplicate, name, organization, inactive and absent-reference discrepancies. Live fixture setup must reproduce the same business evidence; Google IDs will differ from local fixture IDs.
7. Export CSV, confirming only verified rows and actual evidence IDs.
8. Temporarily configure an unreachable directory and run a new objective. Expect failed run/source events and no fabricated verified rows. Restore configuration afterward.
9. Disconnect/revoke the test OAuth authorization, then run again; verify failure/review is truthful.

## n8n

1. Import/publish each workflow and assign least-privilege OAuth plus Header Auth credentials.
2. An unauthenticated webhook request must fail; invalid EVT identifiers must fail validation.
3. Trigger each valid production webhook; confirm `data` is an array and `complete=true`, with actual Google records or HTTP directory data.
4. Switch backend transport to n8n and repeat an agent run. Inspect corresponding n8n executions and FastAPI execution history.
5. Exercise an empty mailbox, a >30-message search, a malformed directory and a failed Google credential. Empty data must be distinguished from failure; bounded truncation must fail, not silently claim completeness.
6. Restart n8n and confirm workflows/credentials survive through persistent PostgreSQL and a stable encryption key.

## Public deployment

Record only actual verified URLs. Check HTTPS frontend, API readiness, source endpoint, exact CORS, login/logout/reload, credentialed fetch, CSV and durable conversations. Start a run, interrupt/restart the backend, wait for lease recovery and confirm results/history. Record cold-start behavior and database provider retention. Capture screenshots only from real executions and redact account identifiers or credentials.
