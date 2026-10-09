# Known limitations and next improvements

## Outstanding external verification

No Gemini key, authorized dedicated Google account or hosting access was supplied. Live semantic answer quality, real Gmail/Calendar operations, public directory retrieval, public RAG deployment and credentialed n8n execution remain unverified. Local fixture mode and contract tests are separate evidence; they do not fulfill those live requirements.

## Deliberate scope

- One shared demo operator; no multi-user role model, password recovery or tenant separation.
- Small curated corpus, whole-record chunks and exact vector scans. No pgvector ANN index; adopt one when latency/corpus size warrants it.
- Pydantic output validation and actual citation identity checks cannot prove that every generated assertion is entailed; complete live retrieval/grounding evaluation.
- Ambiguous intent handling relies on Gemini returning clarification/unsupported output and requires live grading. Fixture answers only expose records, rather than simulating generated reasoning.
- Source count limits reject truncation rather than paginate indefinitely: Calendar 100 results, Gmail 30 messages, HTTP 500 rows. Tune safe limits for real operations.
- Plain-text email bodies only; HTML-only registrations become incomplete evidence. Add controlled HTML-to-text parsing if required.
- Unresolved runs end in review_required with staff notes. They do not suspend on LangGraph's interactive interrupt API or support approval overriding deterministic rules.
- A single worker polls a durable queue. Checkpoint/node events are at-least-once across interruption; live service reads can repeat after recovery. No external writes are performed.
- Additive schema version-1 initialization, not production migration history. Use versioned migrations before evolving deployed tables.
- Structured logs capture stage/outcome but do not yet provide metrics, distributed tracing, run cancellation or a separate worker service.
- Short shared login throttle and active-run caps suit a private assessment; add gateway rate limits and stronger brute-force defense before broader public use.
- Managed persistent state survives backend restarts, but sleeping free hosts cannot guarantee unattended execution.
- Static published directory and ingested knowledge snapshot must be synchronized deliberately. Add an explicit directory content version/checksum to agent evidence next.
- Database logical references currently use application validation rather than foreign-key constraints; add relational constraints and retention jobs for production lifecycle management.
- Local n8n pins the tested stable 2.42.6 image digest; repeat import and execution checks before updating `N8N_IMAGE`. Python-runner warning is irrelevant to these JavaScript-only workflows.

## Priorities

First supply account access, execute the live checklist and record real deployment evidence. Then strengthen migrations/constraints, add real model regression evaluation, durable queue monitoring and field-level source spans. At larger scale use pgvector with calibrated recall, pagination and async provider I/O; retain exact IDs, source hierarchy and deterministic verification behavior.
