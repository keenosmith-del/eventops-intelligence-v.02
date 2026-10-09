# Security design

## Trust boundaries

The browser holds an opaque session cookie, never a Gemini key, OAuth secret, database password or refresh token. A SHA-256 hash of the randomly generated cookie token is stored with server-side expiry in PostgreSQL. Production cookies are HTTP-only and secure; deployment uses a deliberate SameSite policy. Password comparison uses constant-time comparison of digests. One shared operator is an assessment choice, not enterprise identity management.

All mutations require the configured exact browser Origin, including login. CORS allows only that origin and credentials. Account-bound reads require the cookie. The database-backed login throttle provides a short delay and the API limits active run admission to three; production abuse protection needs gateway-level limits and stronger lockout.

OAuth uses a one-use random state stored hashed, bound to the session and valid for ten minutes. Both state and current session must be valid at callback. Google tokens are encrypted with Fernet before PostgreSQL storage. The encryption key and client secret remain in backend configuration. Callback authorization covers read-only Calendar events and Gmail. Removing locally saved credentials does not revoke the remote Google grant; revoke it in the test account's security settings when retiring the demonstration.

## Model and tool policy

- Tool names and event identifiers are allowlisted. Model-generated function calls are validated before any adapter runs.
- Directory location and calendar ID are operator configuration. The model cannot supply arbitrary URLs, inbox filters, credentials or writes.
- Objectives and external email bodies are untrusted. Extraction prompts isolate them as serialized data and forbid following embedded instructions.
- Pydantic rejects unknown extraction fields. Source IDs must belong to the actual fetched messages. Submitted field strings must occur in their source text; fabricated fields fail extraction.
- Deterministic verification owns final status. The model cannot overwrite rules or mark a discrepancy verified.
- Requests have explicit connection/read timeouts, bounded retries and response size/count limits. Redirects are not followed. HTTP directory must use HTTPS in live mode.
- The configured directory URL is a trusted-operator allowlist, not a generalized network sandbox; restrict egress in production if administrators are not fully trusted.
- n8n requires Header Auth; exported workflow JSON contains placeholder credential references only. Editor/admin access must be protected separately.

## Data and output

Only fictional directory records are intentionally public. Gmail bodies, Google tokens, agent state and execution histories remain behind backend or n8n authentication. Operational evidence can include message contents in checkpoints; use only dedicated synthetic accounts. Restrict database/admin access and define retention before real organizational use. API caches are disabled; content-type sniffing is blocked. Errors omit provider response bodies/tokens. CSV export excludes unresolved records and prefixes formula-like values to avoid spreadsheet execution.

Environment files, caches, runtime databases and local credentials are ignored by Git. Verify staged files before every commit. Rotate exposed secrets; never commit them for convenience. TLS and managed-database SSL are required for production. Frontend deployment cannot compensate for a publicly exposed or unauthenticated n8n editor.
