"""Exercise the real HTTP API against local PostgreSQL, using configured demo credentials."""

import json
import os
import sys
import time
import uuid
from pathlib import Path
import httpx

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
from app.config import settings

cfg = settings()
with httpx.Client(
    base_url=os.environ.get("SMOKE_API_URL", "http://localhost:5050"),
    headers={"Origin": cfg.frontend_origin},
    timeout=120,
) as client:
    assert client.get("/api/health").status_code == 200
    login = client.post(
        "/api/session",
        json={"username": cfg.demo_username, "password": cfg.demo_password},
    )
    assert login.status_code == 200, login.text
    index = client.post("/api/documents/ingest")
    assert index.status_code == 200, index.text
    q = client.post(
        "/api/rag/query", json={"question": "When does registration close for EVT-101?"}
    )
    assert q.status_code == 200, q.text
    cid = q.json()["conversation_id"]
    assert len(client.get("/api/conversations/" + cid).json()) == 2
    payload = {
        "objective": "Prepare a verified attendee list for EVT-101 using calendar invitations, registration emails and published directory.",
        "event_id": "EVT-101",
        "idempotency_key": str(uuid.uuid4()),
    }
    run = client.post("/api/runs", json=payload)
    assert run.status_code == 202, run.text
    rid = run.json()["id"]
    assert client.post("/api/runs", json=payload).json()["id"] == rid
    for _ in range(120):
        state = client.get("/api/runs/" + rid).json()
        if state["status"] not in ("queued", "running"):
            break
        time.sleep(0.5)
    assert state["status"] == "review_required", state
    rows = client.get("/api/runs/" + rid + "/results").json()
    assert len(rows) == 7
    assert sum(r["status"] == "verified" for r in rows) == 1
    exported = client.get("/api/runs/" + rid + "/export.csv")
    assert exported.status_code == 200
    assert (
        "amara@example.org" in exported.text and "ben@example.org" not in exported.text
    )
    assert (
        client.post(
            "/api/runs/" + rid + "/review",
            json={
                "note": "Review noted; correct duplicate registration evidence before rerunning."
            },
        ).status_code
        == 200
    )
    report = {
        "api_url": os.environ.get("SMOKE_API_URL", "http://localhost:5050"),
        "mode": cfg.mode,
        "database": "PostgreSQL",
        "run_id": rid,
        "conversation_id": cid,
        "status": state["status"],
        "records": len(rows),
        "verified": 1,
        "stages": [e["stage"] for e in state["events"]],
        "checks": [
            "health",
            "session",
            "ingestion",
            "RAG contract",
            "durable conversation",
            "idempotent run",
            "worker",
            "verification",
            "CSV",
            "review note",
        ],
        "external_live_services_verified": False,
    }
    (root / "docs/testing/postgres-smoke.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))
