import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from sqlalchemy import select
from app.agent import build_graph
from app.db import Run, Execution, Verification, DB
from app.ai import AI
from app.schemas import Plan
from app.integrations import Tools, ToolFailure


def new_run(db, eid="EVT-101"):
    run = Run(
        owner="operator",
        objective="Prepare a verified attendee list",
        event_id=eid,
        mode="fixture",
        idempotency_key=eid + "-test",
    )
    db.add(run)
    db.commit()
    return run


def invoke(graph, run):
    return graph.invoke(
        {"run_id": run.id, "objective": run.objective, "event_id": run.event_id},
        {"configurable": {"thread_id": run.id}},
    )


def test_real_graph_transitions_and_results(db):
    run = new_run(db)
    state = invoke(build_graph(InMemorySaver()), run)
    db.expire_all()
    assert state["status"] == "review_required"
    assert db.get(Run, run.id).status == "review_required"
    stages = [e.stage for e in db.scalars(select(Execution)).all()]
    assert stages[0] == "planning"
    assert "human_review" in stages
    assert stages[-1] == "outcome"
    assert len(db.scalars(select(Verification)).all()) == 7


def test_tool_failure_is_recorded_without_success(db):
    class Broken(Tools):
        def call(self, tool, eid):
            if tool == "web":
                raise ToolFailure("Directory offline")
            return super().call(tool, eid)

    run = new_run(db, "EVT-102")
    state = invoke(build_graph(InMemorySaver(), tools_factory=Broken), run)
    assert state["status"] == "failed"
    assert state["failures"]["web"] == "Directory offline"
    assert all(r["status"] != "verified" for r in state["results"])


def test_partial_gmail_failure_routes_review(db):
    class Broken(Tools):
        def call(self, tool, eid):
            if tool == "gmail":
                raise ToolFailure("Mailbox unavailable")
            return super().call(tool, eid)

    state = invoke(
        build_graph(InMemorySaver(), tools_factory=Broken), new_run(db, "EVT-102")
    )
    assert state["status"] == "review_required"
    assert all(r["status"] != "verified" for r in state["results"])


def test_conditional_tool_selection(db):
    class Planner(AI):
        def plan(self, *args):
            return Plan(
                event_id="EVT-101",
                tools=["gmail", "web"],
                rationale="Registration-only request",
            )

    state = invoke(build_graph(InMemorySaver(), ai=Planner()), new_run(db))
    assert "calendar" not in state["sources"]
    assert state["status"] == "review_required"


def test_checkpoint_survives_graph_recreation(db, tmp_path):
    run = new_run(db, "EVT-102")
    path = str(tmp_path / "checkpoints.sqlite")
    config = {"configurable": {"thread_id": run.id}}
    with SqliteSaver.from_conn_string(path) as saver:
        g = build_graph(saver)
        g.invoke(
            {"run_id": run.id, "objective": run.objective, "event_id": run.event_id},
            config,
            interrupt_after=["tools"],
        )
        assert g.get_state(config).next
    with SqliteSaver.from_conn_string(path) as saver:
        g = build_graph(saver)
        assert g.get_state(config).values["run_id"] == run.id
        result = g.invoke(None, config)
        assert result["status"] == "completed"
    with DB() as fresh:
        assert fresh.get(Run, run.id).status == "completed"


def test_worker_rejects_fixture_run_after_live_mode_switch(monkeypatch):
    import time
    from types import SimpleNamespace
    from app.agent import Worker
    from app.config import settings
    from app.db import DB, Run, uid

    with DB() as db:
        run = Run(
            owner="operator",
            idempotency_key=uid(),
            objective="Verify EVT-101 registrations",
            event_id="EVT-101",
            mode="fixture",
        )
        db.add(run)
        db.commit()
        rid = run.id
    monkeypatch.setattr(settings(), "mode", "live")
    graph = SimpleNamespace(
        get_state=lambda *args: pytest.fail("Mode mismatch executed the graph")
    )
    worker = Worker(graph)
    worker.start()
    try:
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            with DB() as db:
                current = db.get(Run, rid)
                if current.status == "failed":
                    assert "Run mode differs" in current.error
                    break
            time.sleep(0.01)
        else:
            pytest.fail("Worker failed to reject mismatched run")
    finally:
        worker.close()
