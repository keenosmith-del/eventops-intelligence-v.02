# n8n integration workflows

LangGraph owns high-level planning, state transitions, verification and review. n8n owns selected external reads through authenticated webhooks. The direct adapter remains available for deployments that have not provisioned persistent n8n.

## Import and configure

1. Start `docker compose up -d`; open http://localhost:5678 and create the local n8n owner account.
2. Import `n8n/calendar.json`, `n8n/gmail.json`, `n8n/web.json` through **Import from file**.
3. Create a Header Auth credential with name `X-EventOps-Key` and a strong random value; assign it to every webhook node. Set the same value as backend `N8N_WEBHOOK_SECRET`.
4. Create read-only Google Calendar OAuth2 and Gmail OAuth2 credentials using a dedicated test account. Register n8n's displayed OAuth callback in Google Cloud. Replace the exported `ASSIGN_IN_N8N` credential references through the UI. Calendar URL defaults to `primary`; change it to a URL-encoded dedicated calendar ID where appropriate.
5. In `web.json`'s **Read directory** node, replace `REPLACE_WITH_VERCEL_HOST` with the deployed HTTPS directory host. This is fixed operator configuration, never objective-controlled.
6. After independently confirming unbilled Google access, zero-cost directory hosting and self-hosted n8n, change `ZERO_COST_APPROVED=false` to `true` in each **Validate event** node. Keep exports inactive/blocked until that check. Never enable billing or use n8n Cloud. Test each workflow manually using only fictional data, then publish/activate it. Production paths are `/webhook/eventops-calendar`, `/webhook/eventops-gmail`, `/webhook/eventops-web`; `/webhook-test/` paths work only while n8n listens for a test.
7. Set backend `INTEGRATION_TRANSPORT=n8n`, `N8N_BASE_URL`, and the shared key, then restart.

Requests: `POST` JSON `{"event_id":"EVT-101"}` with the protected header. Success response: `{"data":[...],"complete":true}`. Missing/false completeness, timeout, malformed JSON, wrong credentials or truncated result limits become failed tool events. Nodes do not send email or modify calendars.

## Workflow design

- Calendar: header-auth webhook → allowlisted event validation → OAuth Calendar events API → bounded envelope → response.
- Gmail: webhook → event validation → search up to 20 messages → reject pagination → conditional empty branch or full message reads → decode plain-text bodies → envelope → response.
- HTTP: webhook → event validation → fixed HTTPS directory → schema checks → envelope → response. FastAPI performs full Pydantic validation again.

The workflow code never reads server environment variables. OAuth and webhook secrets reside in n8n's encrypted credential store. The workflow exports contain credential names/placeholders, no tokens. Automatic retries are bounded; high-level retry/resume policy remains in LangGraph/FastAPI. n8n success payload persistence is disabled to minimize mailbox content retention; error executions remain available for diagnosis, with restricted admin access.

Local Docker volumes persist n8n's configuration; its database uses the separate `n8n` PostgreSQL database initialized by `scripts/init-n8n.sql`. Existing volumes created before that SQL was installed require manual database creation. Maintain the encryption key across restarts. Local `N8N_SECURE_COOKIE=false` is for HTTP only; use HTTPS and secure cookies in deployed n8n. Do not expose the editor anonymously or use a sleeping, ephemeral service for durable automation.

`python3 scripts/check_n8n.py` checks JSON wiring and webhook protection; it is not a credentialed execution test. `scripts/build_n8n_workflows.py` reproduces the exports. Exact live validation is in `docs/testing/live-checks.md`.

The default image pins the verified official stable release 2.42.6 by immutable digest. Set `N8N_IMAGE` only for a deliberate update, then repeat import and live checks. This release is documented alongside the [official n8n release notes](https://docs.n8n.io/release-notes/). Image updates do not replace credentialed execution checks.

## Cost controls and limitations

Every checked-in workflow denies external execution with `ZERO_COST_APPROVED=false`, validates one of three fictional event IDs, has a 600-second execution timeout, and limits HTTP node retries to three. Gmail rejects pagination and more than 20 message IDs before fan-out. FastAPI never retries a workflow POST; it reserves 64 HTTP units for Gmail and four each for Calendar/directory, including maximum application node fan-out. OAuth refresh internal to n8n is controlled by its credential implementation, outside FastAPI's individual request accounting. These conservative reservations are not a billing guarantee or an exact downstream meter.

Manual n8n executions bypass FastAPI's global daily counter. Restrict editor/webhook credentials to the operator, execute only bounded test cases, and leave workflows inactive outside the walkthrough. Zero-cost provider/account confirmation is mandatory even for manual runs. There is no verified free durable public n8n host. Actual local import succeeded on 2.42.6; the CLI warns PostgreSQL 16 receives compatibility support only. Upgrade PostgreSQL through a planned backup/restore, never by replacing the version on an existing volume.
