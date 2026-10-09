import csv
import hashlib
import hmac
import io
import json
import logging
import secrets
import time
from contextlib import asynccontextmanager, ExitStack
from urllib.parse import urlencode
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import IntegrityError
from .config import settings, ROOT
from .db import (
    DB,
    Session,
    OAuthState,
    Credential,
    Conversation,
    Message,
    Document,
    Run,
    Execution,
    Verification,
    get_db,
    initialize,
    now,
    log_event,
)
from .schemas import (
    Login,
    Query,
    RunRequest,
    Review,
    HealthResponse,
    SessionResponse,
    StatusResponse,
    DocumentResponse,
    IngestionResponse,
    ConversationResponse,
    MessageResponse,
    QueryResponse,
    RunResponse,
    VerificationResponse,
)
from .rag import ingest, ask
from .ai import ModelFailure
from .integrations import request_json, store_token, ToolFailure
from .agent import build_graph, Worker

cfg = settings()


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(
            {
                "time": now(),
                "level": record.levelname,
                "message": record.getMessage(),
                **{
                    k: getattr(record, k)
                    for k in ["run_id", "stage", "outcome"]
                    if hasattr(record, k)
                },
            }
        )


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.getLogger("eventops").addHandler(handler)
logging.getLogger("eventops").setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app):
    if not cfg.demo_password:
        raise RuntimeError("Set DEMO_PASSWORD in backend/.env before starting")
    if (
        cfg.mode == "live"
        and not cfg.cookie_secure
        and not cfg.frontend_origin.startswith("http://localhost:")
    ):
        raise RuntimeError("Production requires secure cookies")
    initialize()
    with ExitStack() as stack:
        if cfg.worker_enabled:
            if cfg.database_url.startswith("postgresql"):
                from langgraph.checkpoint.postgres import PostgresSaver

                saver = stack.enter_context(
                    PostgresSaver.from_conn_string(cfg.checkpoint_uri)
                )
                saver.setup()
            else:
                from langgraph.checkpoint.sqlite import SqliteSaver

                # Only for isolated fixtures/tests. Deployed state always uses PostgreSQL.
                path = cfg.database_url.removeprefix("sqlite:///") + ".checkpoints"
                saver = stack.enter_context(SqliteSaver.from_conn_string(path))
            worker = Worker(build_graph(saver))
            worker.start()
            app.state.worker = worker
        yield
        if cfg.worker_enabled:
            worker.close()


app = FastAPI(title="EventOps Intelligence", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[cfg.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
    allow_private_network=cfg.frontend_origin.startswith("http://localhost:"),
)


@app.middleware("http")
async def security(request, call_next):
    if request.method in ("POST", "DELETE", "PUT", "PATCH"):
        if request.headers.get("origin") != cfg.frontend_origin:
            return Response("Untrusted request origin", status_code=403)
        try:
            length = int(request.headers.get("content-length", "0") or "0")
        except ValueError:
            return Response("Invalid content length", status_code=400)
        if length > 50000:
            return Response("Request too large", status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def authenticated(request: Request, db: DBSession = Depends(get_db)):
    token = request.cookies.get("eventops_session", "")
    session = db.get(Session, digest(token))
    if not session or session.expires < time.time():
        raise HTTPException(401, "Sign in to continue")
    return cfg.demo_username


def owned_run(run_id, owner, db):
    run = db.get(Run, run_id)
    if not run or run.owner != owner:
        raise HTTPException(404, "Run not found")
    return run


def run_view(run):
    return {
        k: getattr(run, k)
        for k in [
            "id",
            "objective",
            "event_id",
            "mode",
            "status",
            "created_at",
            "updated_at",
            "error",
            "state",
        ]
    }


def verification_view(row):
    return {
        k: getattr(row, k)
        for k in ["id", "run_id", "status", "record", "evidence", "reasons"]
    }


@app.get("/api/health", response_model=HealthResponse)
def health(db: DBSession = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(503, "Database unavailable")
    return {"status": "ok", "mode": cfg.mode}


@app.post("/api/session", response_model=SessionResponse)
def login(payload: Login, response: Response, db: DBSession = Depends(get_db)):
    # Persistent throttle is represented by short-lived session rows, never a process-only counter.
    throttle = "login:demo"
    row = db.get(Session, throttle)
    if row and row.expires > time.time():
        raise HTTPException(429, "Wait a moment before trying again")
    db.merge(Session(id=throttle, expires=time.time() + 2))
    db.commit()
    if not (
        hmac.compare_digest(payload.username, cfg.demo_username)
        and hmac.compare_digest(
            hashlib.sha256(payload.password.encode()).digest(),
            hashlib.sha256(cfg.demo_password.encode()).digest(),
        )
    ):
        raise HTTPException(401, "Incorrect username or password")
    token = secrets.token_urlsafe(32)
    db.add(Session(id=digest(token), expires=time.time() + cfg.session_hours * 3600))
    db.commit()
    response.set_cookie(
        "eventops_session",
        token,
        httponly=True,
        secure=cfg.cookie_secure,
        samesite=cfg.cookie_samesite,
        max_age=cfg.session_hours * 3600,
        path="/",
    )
    return {"username": cfg.demo_username}


@app.get("/api/session", response_model=SessionResponse)
def session(owner=Depends(authenticated)):
    return {"username": owner, "mode": cfg.mode}


@app.delete("/api/session")
def logout(request: Request, response: Response, db: DBSession = Depends(get_db)):
    session = db.get(Session, digest(request.cookies.get("eventops_session", "")))
    if session:
        db.delete(session)
        db.commit()
    response.delete_cookie(
        "eventops_session",
        path="/",
        secure=cfg.cookie_secure,
        samesite=cfg.cookie_samesite,
    )
    return {"status": "signed_out"}


@app.get("/api/status", response_model=StatusResponse)
def status(owner=Depends(authenticated), db: DBSession = Depends(get_db)):
    return {
        "mode": cfg.mode,
        "model": cfg.gemini_model,
        "gemini_configured": bool(cfg.gemini_api_key),
        "google_connected": bool(db.get(Credential, "google")),
        "oauth_configured": bool(
            cfg.google_client_id
            and cfg.google_client_secret
            and cfg.token_encryption_key
        ),
        "directory_configured": bool(cfg.directory_url),
        "transport": cfg.integration_transport,
        "worker_enabled": cfg.worker_enabled,
    }


@app.get("/api/documents", response_model=list[DocumentResponse])
def documents(owner=Depends(authenticated), db: DBSession = Depends(get_db)):
    return [
        {"id": d.id, "name": d.name, "checksum": d.checksum, "ingestion": d.ingestion}
        for d in db.scalars(select(Document)).all()
    ]


@app.post("/api/documents/ingest", response_model=IngestionResponse)
def ingestion(owner=Depends(authenticated), db: DBSession = Depends(get_db)):
    try:
        return ingest(db)
    except ModelFailure as exc:
        raise HTTPException(503, str(exc))
    except ValueError:
        raise HTTPException(422, "Knowledge data failed schema validation")


@app.get("/api/conversations", response_model=list[ConversationResponse])
def conversations(owner=Depends(authenticated), db: DBSession = Depends(get_db)):
    return [
        {"id": c.id, "created_at": c.created_at}
        for c in db.scalars(
            select(Conversation)
            .where(Conversation.owner == owner)
            .order_by(Conversation.created_at.desc())
        ).all()
    ]


@app.get("/api/conversations/{conversation_id}", response_model=list[MessageResponse])
def conversation(
    conversation_id: str, owner=Depends(authenticated), db: DBSession = Depends(get_db)
):
    c = db.get(Conversation, conversation_id)
    if not c or c.owner != owner:
        raise HTTPException(404, "Conversation not found")
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "evidence": m.evidence,
            "details": m.details,
        }
        for m in db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at, Message.id)
        ).all()
    ]


@app.post("/api/rag/query", response_model=QueryResponse)
def query(
    payload: Query, owner=Depends(authenticated), db: DBSession = Depends(get_db)
):
    try:
        return ask(db, owner, payload)
    except LookupError:
        raise HTTPException(404, "Conversation not found")
    except ModelFailure as exc:
        raise HTTPException(502, str(exc))


@app.post("/api/runs", status_code=202, response_model=RunResponse)
def start_run(
    payload: RunRequest, owner=Depends(authenticated), db: DBSession = Depends(get_db)
):
    if not cfg.worker_enabled:
        raise HTTPException(503, "Agent worker is disabled")
    existing = db.scalar(
        select(Run).where(
            Run.owner == owner, Run.idempotency_key == payload.idempotency_key
        )
    )
    if existing:
        if (
            existing.objective != payload.objective
            or existing.event_id != payload.event_id
        ):
            raise HTTPException(
                409, "Idempotency key already belongs to another request"
            )
        return run_view(existing)
    events = json.loads((ROOT / "data/structured/events.json").read_text())
    if payload.event_id not in {e["event_id"] for e in events}:
        raise HTTPException(422, "Unknown assessment event")
    active = db.scalars(
        select(Run).where(Run.owner == owner, Run.status.in_(["queued", "running"]))
    ).all()
    if len(active) >= 3:
        raise HTTPException(429, "At most three active workflows are allowed")
    run = Run(
        owner=owner,
        objective=payload.objective,
        event_id=payload.event_id,
        idempotency_key=payload.idempotency_key,
        mode=cfg.mode,
    )
    db.add(run)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        run = db.scalar(
            select(Run).where(
                Run.owner == owner, Run.idempotency_key == payload.idempotency_key
            )
        )
        if (
            not run
            or run.objective != payload.objective
            or run.event_id != payload.event_id
        ):
            raise HTTPException(409, "Concurrent request conflict")
    return run_view(run)


@app.get("/api/runs", response_model=list[RunResponse])
def runs(owner=Depends(authenticated), db: DBSession = Depends(get_db)):
    return [
        run_view(r)
        for r in db.scalars(
            select(Run)
            .where(Run.owner == owner)
            .order_by(Run.created_at.desc())
            .limit(100)
        ).all()
    ]


@app.get("/api/runs/{run_id}", response_model=RunResponse)
def run(run_id: str, owner=Depends(authenticated), db: DBSession = Depends(get_db)):
    r = owned_run(run_id, owner, db)
    events = [
        {
            "id": e.id,
            "created_at": e.created_at,
            "stage": e.stage,
            "outcome": e.outcome,
            "detail": e.detail,
        }
        for e in db.scalars(
            select(Execution)
            .where(Execution.run_id == run_id)
            .order_by(Execution.created_at)
        ).all()
    ]
    return {**run_view(r), "events": events}


@app.get("/api/runs/{run_id}/results", response_model=list[VerificationResponse])
def results(run_id: str, owner=Depends(authenticated), db: DBSession = Depends(get_db)):
    owned_run(run_id, owner, db)
    return [
        verification_view(r)
        for r in db.scalars(
            select(Verification).where(Verification.run_id == run_id)
        ).all()
    ]


@app.post("/api/runs/{run_id}/review")
def review(
    run_id: str,
    payload: Review,
    owner=Depends(authenticated),
    db: DBSession = Depends(get_db),
):
    r = owned_run(run_id, owner, db)
    if r.status != "review_required":
        raise HTTPException(409, "Run does not require review")
    log_event(
        run_id, "human_review", "noted", {"reviewer": owner, "note": payload.note}
    )
    return {
        "status": "recorded",
        "message": "Review note saved. Correct authoritative data and rerun to resolve discrepancies.",
    }


@app.get("/api/runs/{run_id}/export.csv")
def export(run_id: str, owner=Depends(authenticated), db: DBSession = Depends(get_db)):
    owned_run(run_id, owner, db)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(
        [
            "event_id",
            "participant_id",
            "name",
            "email",
            "organization",
            "status",
            "evidence_ids",
        ]
    )

    def safe(value):
        s = str(value or "")
        return "'" + s if s.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else s

    for row in db.scalars(
        select(Verification).where(
            Verification.run_id == run_id, Verification.status == "verified"
        )
    ).all():
        r = row.record
        writer.writerow(
            [
                safe(r.get(k))
                for k in ["event_id", "participant_id", "name", "email", "organization"]
            ]
            + ["verified", safe(";".join(e["source_id"] for e in row.evidence))]
        )
    return StreamingResponse(
        iter([out.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="verified-{run_id}.csv"'
        },
    )


@app.get("/api/integrations/google/start")
def google_start(
    request: Request, owner=Depends(authenticated), db: DBSession = Depends(get_db)
):
    if not (
        cfg.google_client_id and cfg.google_client_secret and cfg.token_encryption_key
    ):
        raise HTTPException(503, "Configure Google OAuth and token encryption first")
    state = secrets.token_urlsafe(32)
    db.add(
        OAuthState(
            id=digest(state),
            session_id=digest(request.cookies["eventops_session"]),
            expires=time.time() + 600,
        )
    )
    db.commit()
    params = {
        "client_id": cfg.google_client_id,
        "redirect_uri": cfg.google_redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar.events.readonly https://www.googleapis.com/auth/gmail.readonly",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return RedirectResponse(
        "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    )


@app.get("/api/integrations/google/callback")
def google_callback(
    request: Request,
    state: str = "",
    code: str = "",
    error: str = "",
    db: DBSession = Depends(get_db),
):
    saved = db.get(OAuthState, digest(state))
    sid = digest(request.cookies.get("eventops_session", ""))
    session = db.get(Session, sid)
    if (
        not saved
        or saved.expires < time.time()
        or saved.session_id != sid
        or not session
        or session.expires < time.time()
    ):
        raise HTTPException(400, "Invalid or expired OAuth state")
    db.delete(saved)
    db.commit()
    if error or not code:
        raise HTTPException(400, "Google authorization declined")
    try:
        payload = request_json(
            "POST",
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": cfg.google_client_id,
                "client_secret": cfg.google_client_secret,
                "redirect_uri": cfg.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if "access_token" not in payload:
            raise ToolFailure("OAuth token response is incomplete")
        store_token(payload)
    except ToolFailure as exc:
        raise HTTPException(502, str(exc))
    return RedirectResponse(cfg.frontend_origin + "/agent?google=connected")


@app.delete("/api/integrations/google")
def disconnect(owner=Depends(authenticated), db: DBSession = Depends(get_db)):
    token = db.get(Credential, "google")
    if token:
        db.delete(token)
        db.commit()
    return {"status": "disconnected"}
