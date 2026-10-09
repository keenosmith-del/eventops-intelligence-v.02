import hashlib
import json
import math
from sqlalchemy import select, delete
from .config import ROOT, settings
from .db import Document, Chunk, Message, Conversation, now
from .schemas import Event, Policy, Participant
from .ai import AI, ModelFailure

SCHEMAS = {"events.json": Event, "policies.json": Policy, "directory.json": Participant}


def parse_documents():
    result = []
    for filename, schema in SCHEMAS.items():
        raw = (ROOT / "data/structured" / filename).read_text()
        records = [schema.model_validate(r).model_dump() for r in json.loads(raw)]
        if len({r["record_id"] for r in records}) != len(records):
            raise ValueError("Duplicate record identifiers")
        result.append((filename, raw, records))
    return result


def ingest(db, ai=None):
    ai = ai or AI()
    parsed = parse_documents()  # Validate all documents before changing index.
    prepared = []
    for filename, raw, records in parsed:
        checksum = hashlib.sha256(
            (raw + settings().mode + settings().embedding_model + "schema-v1").encode()
        ).hexdigest()
        existing = db.get(Document, filename)
        if existing and existing.checksum == checksum:
            continue
        texts = [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records]
        vectors = ai.embed(texts, "RETRIEVAL_DOCUMENT")
        prepared.append((filename, checksum, records, texts, vectors))
    try:
        for filename, checksum, records, texts, vectors in prepared:
            db.execute(delete(Chunk).where(Chunk.document_id == filename))
            db.merge(
                Document(
                    id=filename,
                    name=filename.removesuffix(".json").title(),
                    checksum=checksum,
                    ingestion={
                        "at": now(),
                        "records": len(records),
                        "embedding": settings().embedding_model
                        if settings().mode == "live"
                        else "fixture-test-double",
                        "dimensions": len(vectors[0]),
                        "mode": settings().mode,
                    },
                )
            )
            for r, text, vector in zip(records, texts, vectors):
                db.add(
                    Chunk(
                        id=f"{filename}:{r['record_id']}",
                        document_id=filename,
                        record_id=r["record_id"],
                        event_id=r.get("event_id"),
                        text=text,
                        vector=vector,
                        source={
                            "file": f"data/structured/{filename}",
                            "record_id": r["record_id"],
                            "event_ids": r.get("event_ids", []),
                            "record": r,
                        },
                    )
                )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"updated_documents": len(prepared), "documents": len(parsed)}


def cosine(a, b):
    if len(a) != len(b):
        raise ModelFailure("Index embedding dimensions differ; re-ingest knowledge")
    return sum(x * y for x, y in zip(a, b)) / (
        math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(x * x for x in b)) or 1
    )


def retrieve(db, question, history, ai):
    intent = ai.intent(question, history)
    docs = db.scalars(select(Document)).all()
    if not docs:
        raise ModelFailure("Knowledge index is empty. Run ingestion first.")
    if any(d.ingestion["mode"] != settings().mode for d in docs):
        raise ModelFailure("Index mode differs; re-ingest knowledge")
    vector = ai.embed([intent.query], "RETRIEVAL_QUERY")[0]
    chunks = db.scalars(select(Chunk)).all()
    if intent.event_id:
        chunks = [
            c
            for c in chunks
            if c.event_id == intent.event_id
            or (
                c.event_id is None
                and (
                    not c.source.get("event_ids")
                    or intent.event_id in c.source["event_ids"]
                )
            )
        ]
    ranked = sorted(
        [(cosine(vector, c.vector), c) for c in chunks],
        key=lambda x: x[0],
        reverse=True,
    )
    evidence = [
        {"id": c.id, "score": round(score, 4), "text": c.text, "source": c.source}
        for score, c in ranked[:8]
        if score >= 0.20
    ]
    return evidence, intent


def ask(db, owner, request, ai=None):
    ai = ai or AI()
    if request.conversation_id:
        conversation = db.get(Conversation, request.conversation_id)
        if not conversation or conversation.owner != owner:
            raise LookupError("Conversation not found")
    else:
        conversation = Conversation(owner=owner)
        db.add(conversation)
        db.flush()
    prior = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(8)
    ).all()
    history = [{"role": m.role, "content": m.content} for m in reversed(prior)]
    evidence, intent = retrieve(db, request.question, history, ai)
    answer = ai.answer(request.question, history, evidence)
    ids = {e["id"] for e in evidence}
    if (
        not set(answer.citations) <= ids
        or (answer.supported and not answer.citations)
        or (not answer.supported and answer.citations)
    ):
        raise ModelFailure("Answer citation contract failed")
    if not answer.supported:
        evidence = []
    details = {
        "supported": answer.supported,
        "citations": answer.citations,
        "query": intent.query,
        "event_id": intent.event_id,
        "mode": settings().mode,
        "retrieved": len(evidence),
        "embedding": settings().embedding_model
        if settings().mode == "live"
        else "fixture-test-double",
    }
    db.add(
        Message(
            conversation_id=conversation.id,
            role="user",
            content=request.question,
            evidence=[],
            details={},
        )
    )
    db.flush()
    db.add(
        Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer.answer,
            evidence=evidence,
            details=details,
        )
    )
    db.commit()
    return {
        "conversation_id": conversation.id,
        **answer.model_dump(),
        "evidence": evidence,
        "retrieval": details,
    }
