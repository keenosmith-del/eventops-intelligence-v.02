import json
import pytest
from sqlalchemy import select, func
from app.db import Chunk, Document, Conversation, Message
from app.rag import ingest, retrieve, ask, parse_documents, cosine
from app.ai import AI, ModelFailure
from app.schemas import Query, Answer, Participant


def test_three_valid_documents_and_record_traceability(db):
    parsed = parse_documents()
    assert len(parsed) == 3
    assert ingest(db)["updated_documents"] == 3
    chunks = db.scalars(select(Chunk)).all()
    assert len(chunks) >= 13
    for c in chunks:
        assert c.source["record_id"] == c.record_id
        assert json.loads(c.text) == c.source["record"]
        assert c.vector


def test_idempotent_ingestion(db):
    ingest(db)
    count = db.scalar(select(func.count()).select_from(Chunk))
    assert ingest(db)["updated_documents"] == 0
    assert db.scalar(select(func.count()).select_from(Chunk)) == count


def test_schema_invalid_email_and_unknown_fields():
    record = json.loads(
        (
            __import__("app.config", fromlist=["ROOT"]).ROOT
            / "data/structured/directory.json"
        ).read_text()
    )[0]
    record["email"] = "bad email"
    with pytest.raises(ValueError):
        Participant.model_validate(record)


def test_vector_ranking_exact_event_and_global_policies(db):
    ingest(db)
    e, intent = retrieve(db, "When is the registration deadline for EVT-101?", [], AI())
    assert intent.event_id == "EVT-101"
    assert "events.json:event-101" in [x["id"] for x in e]
    assert "events.json:event-102" not in [x["id"] for x in e]
    assert cosine([1, 0], [0, 1]) == 0
    assert cosine([1, 1], [1, 1]) == pytest.approx(1)


def test_memory_persists_between_service_instances(db):
    ingest(db)
    r = ask(db, "operator", Query(question="When is EVT-101 scheduled?"))
    db.expire_all()
    r2 = ask(
        db,
        "operator",
        Query(
            question="What is its registration deadline?",
            conversation_id=r["conversation_id"],
        ),
    )
    assert r2["retrieval"]["event_id"] == "EVT-101"
    assert len(db.scalars(select(Message)).all()) == 4
    assert db.get(Conversation, r["conversation_id"])


def test_no_cross_owner_conversation(db):
    ingest(db)
    r = ask(db, "operator", Query(question="When is EVT-101 scheduled?"))
    with pytest.raises(LookupError):
        ask(
            db,
            "stranger",
            Query(
                question="When is EVT-101 scheduled?",
                conversation_id=r["conversation_id"],
            ),
        )


def test_unsupported_question_no_fabricated_citation(db):
    class Unsupported(AI):
        def answer(self, *args):
            return Answer(
                answer="No evidence supports the weather forecast.",
                supported=False,
                citations=[],
            )

    ingest(db)
    r = ask(db, "operator", Query(question="Will it rain next year?"), Unsupported())
    assert not r["supported"]
    assert not r["evidence"]
    assert not r["citations"]


def test_malformed_model_citation_is_rejected(db):
    class Bad(AI):
        def answer(self, *args):
            return Answer(
                answer="Invented fact", supported=True, citations=["imaginary"]
            )

    ingest(db)
    with pytest.raises(ModelFailure):
        ask(db, "operator", Query(question="When is EVT-101 scheduled?"), Bad())


def test_embedding_dimension_mismatch():
    with pytest.raises(ModelFailure):
        cosine([1], [1, 0])


def test_missing_index_is_explicit(db):
    with pytest.raises(ModelFailure, match="empty"):
        retrieve(db, "When is EVT-101?", [], AI())
