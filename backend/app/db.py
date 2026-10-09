import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Text, JSON, Float, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import settings

def now(): return datetime.now(timezone.utc).isoformat()
def uid(): return str(uuid.uuid4())
class Base(DeclarativeBase): pass
class Session(Base):
    __tablename__ = 'sessions'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    expires: Mapped[float] = mapped_column(Float)
class OAuthState(Base):
    __tablename__ = 'oauth_states'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String)
    expires: Mapped[float] = mapped_column(Float)
class Credential(Base):
    __tablename__ = 'credentials'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    encrypted: Mapped[str] = mapped_column(Text)
class Document(Base):
    __tablename__ = 'documents'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    checksum: Mapped[str] = mapped_column(String)
    ingestion: Mapped[dict] = mapped_column(JSON)
class Chunk(Base):
    __tablename__ = 'chunks'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(String, index=True)
    record_id: Mapped[str] = mapped_column(String)
    event_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    text: Mapped[str] = mapped_column(Text)
    vector: Mapped[list] = mapped_column(JSON)
    source: Mapped[dict] = mapped_column(JSON)
class Conversation(Base):
    __tablename__ = 'conversations'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    owner: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[str] = mapped_column(String, default=now)
class Message(Base):
    __tablename__ = 'messages'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    conversation_id: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[str] = mapped_column(String, default=now)
    role: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
class Run(Base):
    __tablename__ = 'runs'
    __table_args__ = (UniqueConstraint('owner', 'idempotency_key'),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    owner: Mapped[str] = mapped_column(String)
    idempotency_key: Mapped[str] = mapped_column(String)
    objective: Mapped[str] = mapped_column(Text)
    event_id: Mapped[str] = mapped_column(String)
    mode: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default='queued')
    created_at: Mapped[str] = mapped_column(String, default=now)
    updated_at: Mapped[str] = mapped_column(String, default=now)
    lease_until: Mapped[float] = mapped_column(Float, default=0)
    state: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
class Execution(Base):
    __tablename__ = 'executions'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    run_id: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[str] = mapped_column(String, default=now)
    stage: Mapped[str] = mapped_column(String)
    outcome: Mapped[str] = mapped_column(String)
    detail: Mapped[dict] = mapped_column(JSON)
class Verification(Base):
    __tablename__ = 'verifications'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String)
    record: Mapped[dict] = mapped_column(JSON)
    evidence: Mapped[list] = mapped_column(JSON)
    reasons: Mapped[list] = mapped_column(JSON)

cfg = settings()
engine = create_engine(cfg.database_url, pool_pre_ping=True, **({'connect_args': {'check_same_thread': False}} if cfg.database_url.startswith('sqlite') else {'pool_recycle': 300}))
DB = sessionmaker(engine, expire_on_commit=False)
def initialize(): Base.metadata.create_all(engine)
def get_db():
    with DB() as db: yield db

def log_event(run_id, stage, outcome, detail):
    import logging
    with DB() as db:
        db.add(Execution(run_id=run_id, stage=stage, outcome=outcome, detail=detail))
        db.commit()
    logging.getLogger('eventops').info('execution', extra={'run_id': run_id, 'stage': stage, 'outcome': outcome})
