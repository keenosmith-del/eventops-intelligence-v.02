"""Real PostgreSQL concurrency/persistence test; no HTTP or SDK calls."""

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
from app import costs
from app.config import settings
from app.db import DB, UsageCounter, engine, initialize, uid

cfg = settings()
if cfg.mode != "fixture" or not cfg.database_url.startswith("postgresql"):
    sys.exit("Requires local fixture PostgreSQL; never makes provider calls.")
initialize()
# Simulated policy and clock affect only this test module's reserve function.
# Separate audit namespace leaves actual current-day usage budgets intact.
audit = "audit-" + uid()
costs.settings = lambda: cfg.model_copy(
    update=dict(
        mode="live",
        external_calls_enabled=True,
        gemini_free_tier_confirmed=True,
        model_daily_limit=3,
        model_operation_limit=2,
    )
)
costs.datetime = SimpleNamespace(
    now=lambda tz: SimpleNamespace(
        date=lambda: SimpleNamespace(isoformat=lambda: audit)
    )
)


def attempt(i):
    try:
        costs.reserve("model", scope=audit + ":" + str(i))
        return True
    except costs.CostPolicyError:
        return False


with ThreadPoolExecutor(max_workers=8) as pool:
    accepted = sum(pool.map(attempt, range(12)))
assert accepted == 3
engine.dispose()
with DB() as db:
    assert db.get(UsageCounter, "day:" + audit + ":model").used == 3
result = dict(
    database="PostgreSQL",
    concurrent_attempts=12,
    accepted=3,
    cap=3,
    persisted_after_connection_reconstruction=True,
    external_calls=0,
)
(root / "docs/testing/budget-check.json").write_text(
    json.dumps(result, indent=2) + "\n"
)
print(json.dumps(result))
