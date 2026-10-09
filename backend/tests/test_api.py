from app.db import Run, Verification
from app.main import cfg


def test_health_and_auth_contract(client):
    assert client.get("/api/health").json()["mode"] == "fixture"
    assert client.get("/api/documents").status_code == 401
    assert (
        client.post(
            "/api/session", json={"username": "operator", "password": "wrong"}
        ).status_code
        == 401
    )


def test_csrf_origin_is_required(client):
    client.headers["origin"] = "https://untrusted.example"
    assert (
        client.post(
            "/api/session", json={"username": "operator", "password": "x"}
        ).status_code
        == 403
    )


def test_login_cookie_logout(signed_in):
    assert signed_in.cookies.get("eventops_session")
    assert signed_in.get("/api/session").json()["username"] == "operator"
    assert signed_in.delete("/api/session").status_code == 200
    assert signed_in.get("/api/session").status_code == 401


def test_api_rag_and_persistent_history(signed_in):
    assert signed_in.post("/api/documents/ingest").status_code == 200
    response = signed_in.post("/api/rag/query", json={"question": "When is EVT-101?"})
    assert response.status_code == 200
    cid = response.json()["conversation_id"]
    assert len(signed_in.get("/api/conversations/" + cid).json()) == 2
    assert len(signed_in.get("/api/documents").json()) == 3


def test_boundary_validation(signed_in):
    assert signed_in.post("/api/rag/query", json={"question": "x"}).status_code == 422
    assert signed_in.get("/api/runs/missing").status_code == 404
    assert (
        signed_in.get("/api/integrations/google/callback?state=invalid").status_code
        == 400
    )


def test_idempotent_run_and_conflict(signed_in, monkeypatch):
    monkeypatch.setattr(cfg, "worker_enabled", True)
    payload = {
        "objective": "Prepare verified attendee list",
        "event_id": "EVT-101",
        "idempotency_key": "repeat-key-01",
    }
    a = signed_in.post("/api/runs", json=payload)
    assert a.status_code == 202
    b = signed_in.post("/api/runs", json=payload)
    assert b.json()["id"] == a.json()["id"]
    payload["event_id"] = "EVT-102"
    assert signed_in.post("/api/runs", json=payload).status_code == 409


def test_csv_contains_only_verified_and_neutralizes_formulas(signed_in, db):
    r = Run(
        owner="operator",
        objective="export",
        event_id="EVT-101",
        mode="fixture",
        idempotency_key="csv-test",
    )
    db.add(r)
    db.flush()
    for i, status in enumerate(["verified", "review_required"]):
        db.add(
            Verification(
                id=str(i),
                run_id=r.id,
                status=status,
                record={
                    "event_id": "EVT-101",
                    "name": '=HYPERLINK("evil")',
                    "email": "safe@example.org",
                },
                evidence=[],
                reasons=[],
            )
        )
    db.commit()
    response = signed_in.get("/api/runs/" + r.id + "/export.csv")
    assert response.status_code == 200
    assert "review_required" not in response.text
    assert "'=HYPERLINK" in response.text


def test_disabled_worker_is_honest(signed_in):
    assert (
        signed_in.post(
            "/api/runs",
            json={
                "objective": "Verify attendee list",
                "event_id": "EVT-101",
                "idempotency_key": "disabled-worker",
            },
        ).status_code
        == 503
    )
