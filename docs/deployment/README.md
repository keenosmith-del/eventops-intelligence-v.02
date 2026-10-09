# Deployment readiness and access blockers

No public application deployment has been performed. Gemini, Google account consent, managed database and hosting authorization were not supplied; the operator explicitly selected implementation plus documented blockers. No paid resources, billing changes or repository settings changes are required or made.

## Free-tier plan

Use Vercel Hobby for this personal assessment frontend and Render Free for FastAPI, with a durable managed PostgreSQL service selected from an account that has a current free allocation. Check current service allowances before creating anything. Render free web services can sleep after inactivity, and Render's free PostgreSQL database expires after 30 days, so it should not be used as permanent assessment storage. Source: [Render free services](https://render.com/docs/free). Vercel Hobby's personal/non-commercial scope fits this fictional assessment; source: [Vercel Hobby](https://vercel.com/docs/plans/hobby).

n8n requires persistent database/configuration and its stable encryption key. No durable free public n8n host is assumed. Run it on an existing always-on machine with protected HTTPS ingress, or select a genuinely free durable host through the operator's account. Do not create a paid disk or paid web service. Direct integration transport permits the live agent to operate while durable public n8n hosting remains unavailable, but the n8n demonstration remains an outstanding assessment requirement.

## Exact operator actions

1. Authorize the repository in the Vercel and Render accounts; no account credentials belong in source.
2. Provision or select managed PostgreSQL without enabling billing. Obtain a connection URL with SSL. Use `postgresql+psycopg://...?...sslmode=require` (only one `?`, use `&` to append parameters). The account must permit LangGraph checkpoint table initialization.
3. Import this Git repository into Render as a Docker web service using the root `backend/Dockerfile` and **Free** instance. `render.yaml` provides configuration; do not choose a paid instance when applying it. The Docker build context is repository root, so synthetic data is included.
4. Set the private environment values listed in `backend/.env.example`. Set `MODE=live`, `COOKIE_SECURE=true`, `COOKIE_SAMESITE=none`, and the exact frontend HTTPS origin. Persistent keys: demo password, Gemini key, OAuth secrets, Fernet key. Do not regenerate Fernet keys on restarts.
5. Import the frontend into Vercel with root directory `frontend`, build `npm run build`, output `dist`. Set `VITE_API_URL` to the actual HTTPS Render URL before building; production must not use localhost.
6. Once the frontend URL is assigned, update backend `FRONTEND_ORIGIN`. Set backend `DIRECTORY_URL` to `https://ACTUAL_FRONTEND_HOST/reference/directory.json`. Fetch this resource and validate the JSON before a live run.
7. Register the actual backend `/api/integrations/google/callback` HTTPS URI in Google Cloud and set `GOOGLE_REDIRECT_URI` accordingly. Complete read-only Google consent from the signed-in app with the dedicated fictional account.
8. Ingest knowledge through authenticated Overview. This performs real embedding calls; successful build/deployment alone is not a RAG demonstration.
9. If using n8n transport, deploy n8n with durable storage and protected editor, import/publish workflows, authorize Google in n8n, configure the directory node, and set HTTPS `N8N_BASE_URL` plus shared secret.
10. Run `docs/testing/live-checks.md`, capture real run IDs and actual deployment URLs, then update the verification report. Failed operations stay recorded as failures.

## Cookies and cold starts

Cross-site frontend/API cookies require Secure + SameSite=None. Some browsers block third-party cookies even with these flags. Prefer frontend/API custom domains on the same registrable domain when already available, or a correctly configured same-origin API proxy. A domain purchase is not assumed. Test session creation and reload in the target browser before the walkthrough.

Render sleeping services stop in-process workers. PostgreSQL retains queued runs/checkpoints; polling after an agent start keeps the active session requesting the backend. If the instance restarts, worker leases become recoverable after at most 90 seconds. There is no guarantee of uninterrupted autonomous execution while a free instance is asleep. For long unattended workflows, an existing always-on host or an approved durable worker service is necessary.

## Account-dependent blockers

| Capability | Required access | Current status |
|---|---|---|
| Live semantic RAG and grounded Gemini answers | Free Gemini API key/quota | Not provided; implemented, unverified |
| Live planning and email extraction | Gemini API key/quota | Not provided; function calls and structured contracts implemented |
| Calendar/Gmail reads | Dedicated test account, OAuth web client and consent | Not provided; adapters implemented |
| Reachable published reference endpoint | Frontend deployment/account | Static resource prepared, public host pending |
| Public RAG application | Vercel, Render and managed PostgreSQL access | Configurations prepared, deployment pending |
| Credentialed n8n tools | OAuth + webhook credentials + published workflows | Local infrastructure/import verification only |
| Durable public n8n | Existing authorized persistent free infrastructure | No host supplied |

The system is implementation-ready for these steps; the mandatory live assessment is not complete until they are executed and verified.
