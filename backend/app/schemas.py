import re
from typing import Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')
class Event(Strict):
    record_id: str
    event_id: str
    name: str
    date: str
    start_time: str
    end_time: str
    timezone: str
    venue: str
    capacity: int = Field(gt=0)
    registration_deadline: str
class Policy(Strict):
    record_id: str
    event_id: str | None
    title: str
    rule: str
    authority: str
class Participant(Strict):
    record_id: str
    participant_id: str
    name: str
    email: str
    organization: str
    active: bool
    event_ids: list[str]
    @field_validator('email')
    @classmethod
    def valid_email(cls, v):
        v = v.strip().lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', v): raise ValueError('Invalid email')
        return v
class Attendee(Strict):
    name: str | None = None
    email: str | None = None
    participant_id: str | None = None
    organization: str | None = None
    event_id: str | None = None
    source_id: str = Field(min_length=1, max_length=300)
    source_type: Literal['calendar', 'gmail']
class Extraction(Strict):
    attendees: list[Attendee] = Field(max_length=100)
class Plan(Strict):
    event_id: str
    tools: list[Literal['calendar', 'gmail', 'web']] = Field(min_length=1, max_length=3)
    rationale: str = Field(max_length=2000)
class Answer(Strict):
    answer: str = Field(max_length=12000)
    supported: bool
    citations: list[str] = Field(max_length=12)
class QueryIntent(Strict):
    query: str = Field(min_length=1, max_length=2000)
    event_id: str | None = None
class Login(Strict):
    username: str = Field(max_length=100)
    password: str = Field(max_length=200)
class Query(Strict):
    question: str = Field(min_length=3, max_length=2000)
    conversation_id: str | None = None
class RunRequest(Strict):
    objective: str = Field(min_length=10, max_length=2000)
    event_id: str = Field(pattern=r'^EVT-\d{3}$')
    idempotency_key: str = Field(min_length=8, max_length=100)
class Review(Strict):
    note: str = Field(min_length=10, max_length=2000)

class HealthResponse(Strict):
    status: str
    mode: str
class SessionResponse(Strict):
    username: str
    mode: str | None = None
class StatusResponse(Strict):
    mode: str
    model: str
    gemini_configured: bool
    google_connected: bool
    oauth_configured: bool
    directory_configured: bool
    transport: str
    worker_enabled: bool
class DocumentResponse(Strict):
    id: str
    name: str
    checksum: str
    ingestion: dict
class IngestionResponse(Strict):
    updated_documents: int
    documents: int
class ConversationResponse(Strict):
    id: str
    created_at: str
class MessageResponse(Strict):
    id: str
    role: str
    content: str
    evidence: list[dict]
    details: dict
class QueryResponse(Answer):
    conversation_id: str
    evidence: list[dict]
    retrieval: dict
class ExecutionResponse(Strict):
    id: str
    created_at: str
    stage: str
    outcome: str
    detail: dict
class RunResponse(Strict):
    id: str
    objective: str
    event_id: str
    mode: str
    status: Literal['queued','running','completed','review_required','failed']
    created_at: str
    updated_at: str
    error: str | None
    state: dict
    events: list[ExecutionResponse] | None = None
class VerificationResponse(Strict):
    id: str
    run_id: str
    status: Literal['verified','unverified','review_required','failed']
    record: dict
    evidence: list[dict]
    reasons: list[str]
