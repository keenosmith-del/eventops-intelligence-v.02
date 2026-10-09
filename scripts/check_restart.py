"""Two-phase session/history check across a manually restarted backend."""

import json
import os
import sys
from pathlib import Path
import httpx

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
from app.config import settings

cfg = settings()
target = os.environ.get("SMOKE_API_URL", "http://localhost:5050")
private = Path("/tmp/eventops-restart-cookie.json")
with httpx.Client(
    base_url=target, headers={"Origin": cfg.frontend_origin}, timeout=30
) as c:
    if sys.argv[1] == "before":
        response = c.post(
            "/api/session",
            json={"username": cfg.demo_username, "password": cfg.demo_password},
        )
        assert response.status_code == 200
        baseline = json.loads((root / "docs/testing/postgres-smoke.json").read_text())
        private.write_text(
            json.dumps(
                {
                    "cookie": c.cookies.get("eventops_session"),
                    "run_id": baseline["run_id"],
                    "conversation_id": baseline["conversation_id"],
                }
            )
        )
        private.chmod(0o600)
        print(
            "Session and persisted record IDs saved privately for restart verification."
        )
    else:
        saved = json.loads(private.read_text())
        c.cookies.set(
            "eventops_session", saved["cookie"], domain="localhost.local", path="/"
        )
        assert c.get("/api/session").status_code == 200
        assert (
            c.get("/api/runs/" + saved["run_id"]).json()["status"] == "review_required"
        )
        assert len(c.get("/api/conversations/" + saved["conversation_id"]).json()) == 2
        assert len(c.get("/api/runs/" + saved["run_id"] + "/results").json()) == 7
        (root / "docs/testing/restart-check.json").write_text(
            json.dumps(
                {
                    "database": "PostgreSQL",
                    "session_survived": True,
                    "conversation_survived": True,
                    "run_survived": True,
                    "verification_records_survived": 7,
                },
                indent=2,
            )
            + "\n"
        )
        private.unlink()
        print(
            "PostgreSQL session, conversation, run and verification records survived backend restart."
        )
