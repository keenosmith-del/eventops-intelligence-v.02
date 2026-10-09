import httpx
import pytest
from app.integrations import request_json, ToolFailure, decode_body, Tools
from app.ai import AI, ModelFailure
from app.config import settings


def test_malformed_external_json(monkeypatch):
    class Client:
        def __init__(self, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def request(self, *args, **kw):
            return httpx.Response(
                200,
                content=b"broken",
                request=httpx.Request("GET", "https://example.org"),
            )

    monkeypatch.setattr("app.integrations.reserve", lambda *args, **kw: None)
    monkeypatch.setattr(httpx, "Client", Client)
    with pytest.raises(ToolFailure, match="malformed"):
        request_json("GET", "https://example.org")


def test_http_retry_is_bounded(monkeypatch):
    calls = []

    class Client:
        def __init__(self, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def request(self, *args, **kw):
            calls.append(1)
            raise httpx.ConnectError("offline")

    monkeypatch.setattr("app.integrations.reserve", lambda *args, **kw: None)
    monkeypatch.setattr(httpx, "Client", Client)
    monkeypatch.setattr("app.integrations.time.sleep", lambda _: None)
    with pytest.raises(ToolFailure):
        request_json("GET", "https://example.org")
    assert len(calls) == 3


def test_live_without_credentials_never_falls_back(monkeypatch):
    ai = AI()
    monkeypatch.setattr(ai.cfg, "mode", "live")
    ai.client = None
    with pytest.raises(ModelFailure):
        ai.embed(["test"], "RETRIEVAL_QUERY")


def test_plain_email_body_decode():
    assert (
        decode_body({"mimeType": "text/plain", "body": {"data": "SGVsbG8"}}) == "Hello"
    )
    assert decode_body({"mimeType": "text/html", "body": {"data": "SGVsbG8"}}) == ""


def test_n8n_workflow_post_is_never_replayed(monkeypatch):
    reservations, calls = [], []

    class Client:
        def __init__(self, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def request(self, *args, **kw):
            calls.append(1)
            raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx, "Client", Client)
    monkeypatch.setattr(
        "app.integrations.reserve", lambda *args, **kw: reservations.append(kw)
    )
    with pytest.raises(ToolFailure):
        request_json(
            "POST", settings().n8n_base_url + "/webhook/eventops-gmail", "run", "gmail"
        )
    assert len(calls) == 1
    assert reservations[0]["units"] == 64


def test_gmail_over_limit_rejected_before_message_fanout(monkeypatch):
    monkeypatch.setattr(settings(), "mode", "live")
    monkeypatch.setattr("app.integrations.google_token", lambda: "mock")
    calls = []

    def response(*args, **kw):
        calls.append(1)
        return {"messages": [{"id": str(i)} for i in range(31)]}

    monkeypatch.setattr("app.integrations.request_json", response)
    with pytest.raises(ToolFailure, match="bounded limit"):
        Tools("test").call("gmail", "EVT-102")
    assert len(calls) == 1
