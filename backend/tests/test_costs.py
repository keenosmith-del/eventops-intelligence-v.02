from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import pytest
from sqlalchemy import select
from app.config import Settings, settings, validate_configuration
from app.costs import CostPolicyError, operation, reserve
from app.db import DB, UsageCounter, engine
from app.ai import AI, ModelFailure
from app.integrations import request_json, ToolFailure


@pytest.fixture
def approved(monkeypatch):
    cfg = settings()
    for key, value in {
        "mode": "live",
        "external_calls_enabled": True,
        "gemini_free_tier_confirmed": True,
        "google_unbilled_confirmed": True,
        "model_daily_limit": 3,
        "model_operation_limit": 2,
    }.items():
        monkeypatch.setattr(cfg, key, value)
    return cfg


def test_fixture_with_key_never_creates_client(monkeypatch):
    monkeypatch.setattr(settings(), "gemini_api_key", "not-a-real-key")
    monkeypatch.setattr(
        "app.ai.genai.Client",
        lambda **kw: pytest.fail("Fixture created external SDK client"),
    )
    assert AI().client is None
    with pytest.raises(ToolFailure, match="disabled"):
        request_json(
            "GET", "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        )


def test_key_is_not_free_tier_confirmation(approved, monkeypatch):
    monkeypatch.setattr(approved, "gemini_free_tier_confirmed", False)
    with pytest.raises(CostPolicyError, match="confirmation"):
        reserve("model")
    with DB() as db:
        assert not db.scalars(select(UsageCounter)).all()


def test_operation_limit_survives_new_connection(approved):
    with operation("persisted-run"):
        reserve("model")
        reserve("model")
    engine.dispose()
    with operation("persisted-run"), pytest.raises(CostPolicyError, match="exhausted"):
        reserve("model")
    with DB() as db:
        assert db.get(UsageCounter, "operation:persisted-run:model").used == 2
        assert (
            sum(
                c.used
                for c in db.scalars(select(UsageCounter))
                if c.id.startswith("day:")
            )
            == 2
        )


def test_daily_budget_is_atomic_across_workers(approved):
    def attempt(i):
        try:
            reserve("model", scope=str(i))
            return True
        except CostPolicyError:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(12))) == 3


def test_endpoint_allowlist_and_attestation(approved):
    with pytest.raises(CostPolicyError, match="allowlisted"):
        reserve("http", url="https://untrusted.example.com")
    reserve("http", url="https://oauth2.googleapis.com/token")
    with pytest.raises(CostPolicyError, match="Unsafe"):
        reserve("http", url="https://user:secret@oauth2.googleapis.com/token")


def test_oversized_model_input_rejected_before_sdk(approved):
    ai = AI()
    ai.client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kw: pytest.fail("SDK called"))
    )
    with pytest.raises(ModelFailure, match="input exceeds"):
        ai.structured(SimpleNamespace(), "x" * 60001)


def test_no_evidence_abstains_without_model(approved):
    ai = AI()
    assert not ai.answer("Unknown?", [], []).supported


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"database_url": "sqlite:///temporary.sqlite"}, "PostgreSQL"),
        ({"cookie_secure": False}, "HTTPS"),
        ({"frontend_origin": "http://localhost:5173"}, "HTTPS"),
        ({"database_url": "postgresql+psycopg://u:p@db.example/test"}, "SSL"),
    ],
)
def test_production_rejects_unsafe_configuration(changes, message):
    values = dict(
        environment="production",
        mode="fixture",
        cookie_secure=True,
        frontend_origin="https://frontend.example",
        database_url="postgresql+psycopg://u:p@db.example/test?sslmode=require",
    )
    values.update(changes)
    with pytest.raises(ValueError, match=message):
        validate_configuration(Settings(_env_file=None, **values))


def test_local_and_production_configuration_validated_separately():
    assert (
        validate_configuration(
            Settings(
                _env_file=None, mode="fixture", database_url="sqlite:///local.sqlite"
            )
        ).environment
        == "local"
    )
    assert (
        validate_configuration(
            Settings(
                _env_file=None,
                environment="production",
                mode="fixture",
                cookie_secure=True,
                frontend_origin="https://frontend.example",
                database_url="postgresql+psycopg://u:p@db.example/test?sslmode=require",
            )
        ).environment
        == "production"
    )


def test_limits_cannot_be_unrestricted():
    with pytest.raises(ValueError):
        Settings(_env_file=None, model_daily_limit=100000)
    with pytest.raises(ValueError, match="audited"):
        validate_configuration(Settings(_env_file=None, gemini_model="paid-model"))


def test_transient_model_failures_consume_budget(approved, monkeypatch):
    from google.genai import errors
    from app.schemas import Answer

    calls = []

    def fail(**kw):
        calls.append(1)
        raise errors.APIError(429, {"error": {"message": "quota"}})

    ai = AI()
    ai.client = SimpleNamespace(models=SimpleNamespace(generate_content=fail))
    monkeypatch.setattr("app.ai.time.sleep", lambda _: None)
    with operation("retry"), pytest.raises(ModelFailure, match="budget exhausted"):
        ai.structured(Answer, "test")
    assert len(calls) == 2
