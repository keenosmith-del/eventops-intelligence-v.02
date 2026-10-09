
CREATE TABLE chunks (
	id VARCHAR NOT NULL,
	document_id VARCHAR NOT NULL,
	record_id VARCHAR NOT NULL,
	event_id VARCHAR,
	text TEXT NOT NULL,
	vector JSON NOT NULL,
	source JSON NOT NULL,
	PRIMARY KEY (id)
)

;
CREATE INDEX ix_chunks_document_id ON chunks (document_id);
CREATE INDEX ix_chunks_event_id ON chunks (event_id);

CREATE TABLE conversations (
	id VARCHAR NOT NULL,
	owner VARCHAR NOT NULL,
	created_at VARCHAR NOT NULL,
	PRIMARY KEY (id)
)

;
CREATE INDEX ix_conversations_owner ON conversations (owner);

CREATE TABLE credentials (
	id VARCHAR NOT NULL,
	encrypted TEXT NOT NULL,
	PRIMARY KEY (id)
)

;

CREATE TABLE documents (
	id VARCHAR NOT NULL,
	name VARCHAR NOT NULL,
	checksum VARCHAR NOT NULL,
	ingestion JSON NOT NULL,
	PRIMARY KEY (id)
)

;

CREATE TABLE executions (
	id VARCHAR NOT NULL,
	run_id VARCHAR NOT NULL,
	created_at VARCHAR NOT NULL,
	stage VARCHAR NOT NULL,
	outcome VARCHAR NOT NULL,
	detail JSON NOT NULL,
	PRIMARY KEY (id)
)

;
CREATE INDEX ix_executions_run_id ON executions (run_id);

CREATE TABLE messages (
	id VARCHAR NOT NULL,
	conversation_id VARCHAR NOT NULL,
	created_at VARCHAR NOT NULL,
	role VARCHAR NOT NULL,
	content TEXT NOT NULL,
	evidence JSON NOT NULL,
	details JSON NOT NULL,
	PRIMARY KEY (id)
)

;
CREATE INDEX ix_messages_conversation_id ON messages (conversation_id);

CREATE TABLE oauth_states (
	id VARCHAR NOT NULL,
	session_id VARCHAR NOT NULL,
	expires FLOAT NOT NULL,
	PRIMARY KEY (id)
)

;

CREATE TABLE runs (
	id VARCHAR NOT NULL,
	owner VARCHAR NOT NULL,
	idempotency_key VARCHAR NOT NULL,
	objective TEXT NOT NULL,
	event_id VARCHAR NOT NULL,
	mode VARCHAR NOT NULL,
	status VARCHAR NOT NULL,
	created_at VARCHAR NOT NULL,
	updated_at VARCHAR NOT NULL,
	lease_until FLOAT NOT NULL,
	state JSON NOT NULL,
	error TEXT,
	PRIMARY KEY (id),
	UNIQUE (owner, idempotency_key)
)

;

CREATE TABLE sessions (
	id VARCHAR NOT NULL,
	expires FLOAT NOT NULL,
	PRIMARY KEY (id)
)

;

CREATE TABLE usage_counters (
	id VARCHAR NOT NULL,
	used INTEGER NOT NULL,
	PRIMARY KEY (id)
)

;

CREATE TABLE verifications (
	id VARCHAR NOT NULL,
	run_id VARCHAR NOT NULL,
	status VARCHAR NOT NULL,
	record JSON NOT NULL,
	evidence JSON NOT NULL,
	reasons JSON NOT NULL,
	PRIMARY KEY (id)
)

;
CREATE INDEX ix_verifications_run_id ON verifications (run_id);
