-- Migration: create audit_log table (used 020 to avoid conflicts)
CREATE TABLE IF NOT EXISTS audit_log (
    id           SERIAL PRIMARY KEY,
    event_type   VARCHAR(64)  NOT NULL,
    actor_id     INT          REFERENCES accounts(aid) ON DELETE SET NULL,
    actor_email  VARCHAR(256),              -- snapshot at time of event
    target_id    INT          REFERENCES accounts(aid) ON DELETE SET NULL,
    target_email VARCHAR(256),             -- snapshot at time of event
    detail       TEXT,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
 
CREATE INDEX IF NOT EXISTS idx_audit_log_event_type ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);