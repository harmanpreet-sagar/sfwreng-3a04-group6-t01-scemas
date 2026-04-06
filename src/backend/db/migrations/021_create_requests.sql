-- Migration 021: create pending_requests table
 
CREATE TABLE IF NOT EXISTS pending_requests (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(128) NOT NULL,
    email        VARCHAR(256) NOT NULL UNIQUE,
    clearance    VARCHAR(64)  NOT NULL DEFAULT 'operator',
    reason       TEXT,
    requested_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
 
CREATE INDEX IF NOT EXISTS idx_pending_requests_email ON pending_requests(email);