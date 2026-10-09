"""Verify unfinished LangGraph state survives PostgreSQL saver reconstruction."""

import json
import time
import sys
from pathlib import Path
from langgraph.checkpoint.postgres import PostgresSaver

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
from app.config import settings
from app.db import DB, Run, uid
from app.agent import build_graph

cfg = settings()
if cfg.mode != "fixture" or not cfg.database_url.startswith("postgresql"):
    sys.exit("This isolated checkpoint check requires fixture mode with PostgreSQL.")
with DB() as db:
    r = Run(
        owner=cfg.demo_username,
        objective="Prepare a verified EVT-103 attendee list",
        event_id="EVT-103",
        mode="fixture",
        idempotency_key=uid(),
        status="running",
        lease_until=time.time() + 120,
    )
    db.add(r)
    db.commit()
    rid = r.id
config = {"configurable": {"thread_id": rid}}
with PostgresSaver.from_conn_string(cfg.checkpoint_uri) as saver:
    saver.setup()
    g = build_graph(saver)
    g.invoke(
        {"run_id": rid, "objective": r.objective, "event_id": r.event_id},
        config,
        interrupt_after=["tools"],
    )
    assert g.get_state(config).next
with PostgresSaver.from_conn_string(cfg.checkpoint_uri) as fresh:
    g = build_graph(fresh)
    saved = g.get_state(config)
    assert saved.values["sources"] and saved.next
    outcome = g.invoke(None, config)
    assert outcome["status"] == "completed"
with DB() as db:
    assert db.get(Run, rid).status == "completed"
result = {
    "database": "PostgreSQL",
    "run_id": rid,
    "checkpoint_reconstructed": True,
    "pending_state_resumed": True,
    "final_status": outcome["status"],
    "verified_records": len(outcome["results"]),
}
(root / "docs/testing/checkpoint-check.json").write_text(
    json.dumps(result, indent=2) + "\n"
)
print(json.dumps(result, indent=2))
