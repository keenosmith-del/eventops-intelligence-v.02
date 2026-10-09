"""Fail-closed policy and durable atomic attempt budgets, never billing inference."""

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from functools import wraps
from urllib.parse import urlparse

from .config import settings
from .db import DB, UsageCounter, uid

_scope = ContextVar("external_operation", default=None)


class CostPolicyError(RuntimeError):
    pass


@contextmanager
def operation(identifier=None):
    token = _scope.set(identifier or uid())
    try:
        yield
    finally:
        _scope.reset(token)


def bounded_operation(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        with operation():
            return fn(*args, **kwargs)

    return wrapped


def reserve(kind, *, url=None, scope=None, units=1):
    cfg = settings()
    if cfg.mode != "live" or not cfg.external_calls_enabled:
        raise CostPolicyError("External calls disabled by zero-cost policy")
    if kind == "model":
        approved = cfg.gemini_free_tier_confirmed
        daily, per_operation = cfg.model_daily_limit, cfg.model_operation_limit
    else:
        parsed = urlparse(url or "")
        if parsed.username or parsed.password or parsed.fragment:
            raise CostPolicyError("Unsafe external endpoint")
        if parsed.scheme == "https" and parsed.hostname in (
            "www.googleapis.com",
            "gmail.googleapis.com",
            "oauth2.googleapis.com",
        ):
            approved = cfg.google_unbilled_confirmed
        elif url == cfg.directory_url and parsed.scheme == "https" and parsed.hostname:
            approved = cfg.directory_zero_cost_confirmed
        elif (url or "").startswith(
            cfg.n8n_base_url.rstrip("/") + "/webhook/eventops-"
        ) and (
            parsed.scheme == "https"
            or (
                parsed.scheme == "http"
                and parsed.hostname in ("localhost", "127.0.0.1")
            )
        ):
            approved = (
                cfg.n8n_zero_cost_confirmed
                and cfg.google_unbilled_confirmed
                and cfg.directory_zero_cost_confirmed
            )
        else:
            raise CostPolicyError("External endpoint is not allowlisted")
        daily, per_operation = cfg.http_daily_limit, cfg.http_operation_limit
    if not approved:
        raise CostPolicyError("Unbilled provider/account confirmation is required")
    if not isinstance(units, int) or units < 1:
        raise CostPolicyError("Invalid budget reservation")
    identifier = scope or _scope.get() or uid()
    day = datetime.now(UTC).date().isoformat()
    # Both reservations commit together; denied attempts cannot refund earlier calls.
    with DB() as db:
        dialect = db.bind.dialect.name
        if dialect == "postgresql":
            from sqlalchemy.dialects.postgresql import insert
        elif dialect == "sqlite":
            from sqlalchemy.dialects.sqlite import insert
        else:
            raise CostPolicyError("Unsupported durable budget store")
        for key, limit in (
            (f"day:{day}:{kind}", daily),
            (f"operation:{identifier}:{kind}", per_operation),
        ):
            statement = insert(UsageCounter).values(id=key, used=units)
            statement = statement.on_conflict_do_update(
                index_elements=[UsageCounter.id],
                set_={"used": UsageCounter.used + units},
                where=UsageCounter.used + units <= limit,
            ).returning(UsageCounter.used)
            if units > limit or db.scalar(statement) is None:
                raise CostPolicyError(
                    "External attempt budget exhausted; no paid fallback"
                )
        db.commit()
