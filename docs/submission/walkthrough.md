# Technical walkthrough - 25 minutes

## Preparation

Start PostgreSQL, n8n, backend and frontend independently. Check health, mode, configured credentials and populated fictional data. Use live mode only when the live checklist has actually passed; otherwise introduce the local fixture demonstration and its outstanding access requirements clearly. Open architecture diagrams and test evidence in advance. Do not display environment secrets.

| Time | Demonstration | Engineering point |
|---|---|---|
| 0-2 min | Explain operational problem and sign in | One coherent workflow, minimal server session |
| 2-4 min | Overview, source counts and truthful integration state | Database-backed state; no fabricated activity |
| 4-8 min | Ask factual/multi-record RAG questions, expand evidence, ask unsupported question | Semantic embeddings, record chunking, exact IDs, citation contract |
| 8-10 min | Follow-up and browser refresh | Durable conversation context |
| 10-15 min | Start EVT-101 attendee workflow and inspect planning/tools | Gemini function calls, LangGraph conditional execution, actual source outcomes |
| 15-18 min | Inspect normalized results and discrepancies | Deterministic authority hierarchy, duplicates/missing data, original provenance |
| 18-20 min | Save review note and export verified CSV | Human escalation without model overriding rules |
| 20-22 min | Execution history and checkpoint/restart evidence | Idempotent admission, durable queue, at-least-once recovery |
| 22-24 min | n8n workflows and architecture/decisions | Integration ownership, credentials and read-only policy |
| 24-25 min | Tests, deployment status and limitations | Evidence-based delivery; live blockers and scaling choices |

## Questions to prepare

- Why whole-record chunking? It preserves structure and traceability for short records.
- Why no pgvector? Thirteen records justify exact vector ranking; measured scale would change this choice.
- Where does model reasoning stop? Tool planning, intent and extraction are model tasks; final verification remains deterministic.
- How does prompt injection fail safely? Tool names/IDs/URLs are constrained and source text cannot grant writes or override rules.
- What happens on directory failure? Persist the failed source and outcome; never export fabricated verified attendees.
- How does recovery work? PostgreSQL leases and checkpoints resume pending work after restart; repeated reads and duplicate event logs are possible.
- Does a review note approve an attendee? No. Staff correct evidence and rerun; notes provide an audit trail.
- What remains before a live submission? Account authorization, live evaluation, genuine Google/n8n execution, public directory and verified deployment URLs.

## Submission materials

Use the executive brief for the opening discussion; the engineering report supports deeper implementation review. Architecture Markdown includes system, RAG, graph, integration and verification Mermaid diagrams. Test JSON and real screenshots support the local validation claims. Do not present fixture screenshots as live integration evidence.
