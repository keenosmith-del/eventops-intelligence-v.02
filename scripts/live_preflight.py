"""Report credential/policy blockers explicitly; never contact a provider."""

import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
from app.config import settings

cfg = settings()
checks = {
    "live_mode": cfg.mode == "live",
    "external_calls_enabled": cfg.external_calls_enabled,
    "gemini_key": bool(cfg.gemini_api_key),
    "gemini_models_unbilled_confirmed": cfg.gemini_free_tier_confirmed,
    "google_oauth_client": bool(cfg.google_client_id and cfg.google_client_secret),
    "google_unbilled_confirmed": cfg.google_unbilled_confirmed,
    "token_encryption_key": bool(cfg.token_encryption_key),
    "directory_url": bool(cfg.directory_url),
    "directory_zero_cost_confirmed": cfg.directory_zero_cost_confirmed,
}
if cfg.integration_transport == "n8n":
    checks.update(
        n8n_zero_cost_confirmed=cfg.n8n_zero_cost_confirmed,
        n8n_webhook_secret=bool(cfg.n8n_webhook_secret),
    )
missing = [key for key, ok in checks.items() if not ok]
result = dict(
    status="blocked"
    if missing
    else "configuration_ready_account_evidence_still_required",
    missing=missing,
    external_calls=0,
    live_verified=False,
    deployment_verified=False,
)
(root / "docs/testing/live-preflight.json").write_text(
    json.dumps(result, indent=2) + "\n"
)
print(json.dumps(result, indent=2))
sys.exit(2 if missing else 0)
