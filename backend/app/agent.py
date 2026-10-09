import threading
import time
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy import delete, or_, select

from .ai import AI
from .config import settings
from .costs import operation
from .db import DB, Run, Verification, log_event, now
from .integrations import Tools
from .schemas import Attendee
from .verify import verify


class State(TypedDict, total=False):
    run_id: str
    objective: str
    event_id: str
    plan: dict
    pending: list[str]
    sources: dict
    failures: dict
    attendees: list[dict]
    results: list[dict]
    status: str


def build_graph(checkpointer, ai=None, tools_factory=Tools):
    ai = ai or AI()

    def plan(s):
        log_event(s["run_id"], "planning", "started", {})
        p = ai.plan(s["objective"], s["event_id"]).model_dump()
        log_event(s["run_id"], "planning", "completed", p)
        return {
            "plan": p,
            "pending": p["tools"],
            "sources": {},
            "failures": {},
            "status": "running",
        }

    def tools(s):
        tool = s["pending"][0]
        sources = dict(s["sources"])
        failures = dict(s["failures"])
        log_event(
            s["run_id"],
            tool,
            "started",
            {"mode": __import__("app.config", fromlist=["settings"]).settings().mode},
        )
        try:
            data = tools_factory(s["run_id"]).call(tool, s["event_id"])
            sources[tool] = data
            log_event(s["run_id"], tool, "completed", {"records": len(data)})
        except Exception as exc:
            failures[tool] = (
                str(exc) if isinstance(exc, RuntimeError) else "Malformed tool response"
            )
            log_event(s["run_id"], tool, "failed", {"error": failures[tool]})
        return {"pending": s["pending"][1:], "sources": sources, "failures": failures}

    def extract(s):
        attendees = []
        failures = dict(s["failures"])
        try:
            for event in s["sources"].get("calendar", []):
                for a in event.get("attendees", []):
                    if a.get("responseStatus") == "declined":
                        continue
                    attendees.append(
                        Attendee(
                            name=a.get("displayName"),
                            email=a.get("email"),
                            event_id=s["event_id"],
                            source_id=event["id"]
                            + ":"
                            + (a.get("email") or str(len(attendees))),
                            source_type="calendar",
                        ).model_dump()
                    )
        except (ValueError, KeyError, TypeError):
            failures["calendar"] = "Malformed calendar attendees"
            attendees = []
        if "gmail" in s["sources"]:
            try:
                attendees.extend(
                    a.model_dump()
                    for a in ai.extract(s["sources"]["gmail"], s["event_id"])
                )
            except Exception as exc:
                failures["gmail_extraction"] = (
                    str(exc)
                    if isinstance(exc, RuntimeError)
                    else "Invalid email extraction"
                )
        log_event(
            s["run_id"],
            "extraction",
            "partial" if failures else "completed",
            {"attendees": len(attendees), "failures": failures},
        )
        return {"attendees": attendees, "failures": failures}

    def verification(s):
        missing = set(["calendar", "gmail", "web"]) - set(s["sources"])
        failures = list(set(s["failures"]) | missing)
        results = verify(
            s["attendees"], s["sources"].get("web", []), s["event_id"], failures
        )
        status = (
            "failed"
            if not results or "web" in failures
            else (
                "review_required"
                if failures or any(r["status"] != "verified" for r in results)
                else "completed"
            )
        )
        log_event(
            s["run_id"],
            "verification",
            status,
            {
                "records": len(results),
                "statuses": {
                    k: sum(r["status"] == k for r in results)
                    for k in ["verified", "unverified", "review_required"]
                },
            },
        )
        return {"results": results, "status": status}

    def review(s):
        log_event(
            s["run_id"],
            "human_review",
            "required",
            {
                "reason": "Unresolved discrepancies; deterministic statuses cannot be overridden by the model."
            },
        )
        return {}

    def finish(s):
        with DB() as db:
            db.execute(delete(Verification).where(Verification.run_id == s["run_id"]))
            for i, r in enumerate(s.get("results", [])):
                db.add(Verification(id=f"{s['run_id']}:{i}", run_id=s["run_id"], **r))
            run = db.get(Run, s["run_id"])
            run.status = s["status"]
            run.state = dict(s)
            run.updated_at = now()
            run.lease_until = 0
            if s["status"] == "failed":
                run.error = "Authoritative source unavailable or no attendee records; inspect execution events"
            db.commit()
        log_event(s["run_id"], "outcome", s["status"], {})
        return {}

    g = StateGraph(State)
    for name, fn in [
        ("plan", plan),
        ("tools", tools),
        ("extract", extract),
        ("verify", verification),
        ("review", review),
        ("finish", finish),
    ]:
        g.add_node(name, fn)
    g.add_edge(START, "plan")
    g.add_edge("plan", "tools")
    g.add_conditional_edges("tools", lambda s: "tools" if s["pending"] else "extract")
    g.add_edge("extract", "verify")
    g.add_conditional_edges(
        "verify", lambda s: "review" if s["status"] == "review_required" else "finish"
    )
    g.add_edge("review", "finish")
    g.add_edge("finish", END)
    return g.compile(checkpointer=checkpointer)


class Worker:
    def __init__(self, graph):
        self.graph = graph
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.loop, daemon=True)

    def loop(self):
        while not self.stop.is_set():
            try:
                with DB() as db:
                    run = db.scalar(
                        select(Run)
                        .where(
                            or_(
                                Run.status == "queued",
                                (Run.status == "running")
                                & (Run.lease_until < time.time()),
                            )
                        )
                        .order_by(Run.created_at)
                        .with_for_update(skip_locked=True)
                        .limit(1)
                    )
                    if not run:
                        self.stop.wait(1)
                        continue
                    run.status = "running"
                    run.lease_until = time.time() + 90
                    run.updated_at = now()
                    db.commit()
                    initial = {
                        "run_id": run.id,
                        "objective": run.objective,
                        "event_id": run.event_id,
                    }
                    rid = run.id
                    run_mode = run.mode
                renew_stop = threading.Event()

                def renew(renew_stop=renew_stop, rid=rid):
                    while not renew_stop.wait(20):
                        with DB() as db:
                            r = db.get(Run, rid)
                            if r and r.status == "running":
                                r.lease_until = time.time() + 90
                                db.commit()

                heartbeat = threading.Thread(target=renew, daemon=True)
                heartbeat.start()
                try:
                    if run_mode != settings().mode:
                        raise RuntimeError(
                            "Run mode differs from current configuration; start a new run"
                        )
                    config = {"configurable": {"thread_id": rid}, "recursion_limit": 20}
                    checkpoint = self.graph.get_state(config)
                    with operation(rid):
                        self.graph.invoke(None if checkpoint.next else initial, config)
                except Exception as exc:
                    with DB() as db:
                        r = db.get(Run, rid)
                        r.status = "failed"
                        r.error = (
                            str(exc)
                            if isinstance(exc, RuntimeError)
                            else "Workflow failed; inspect server logs"
                        )
                        r.updated_at = now()
                        r.lease_until = 0
                        db.commit()
                    log_event(
                        rid,
                        "workflow",
                        "failed",
                        {"error": "Execution failed; no successful outcome recorded"},
                    )
                finally:
                    renew_stop.set()
                    heartbeat.join(1)
            except Exception:
                __import__("logging").getLogger("eventops").exception(
                    "worker_iteration_failed"
                )
                self.stop.wait(3)

    def start(self):
        self.thread.start()

    def close(self):
        self.stop.set()
        self.thread.join(65)
