-- Migration: create accounts table (used 019 to avoid merge conflicts)
CREATE TABLE IF NOT EXISTS accounts (
    aid          SERIAL PRIMARY KEY,
    name         VARCHAR(128) NOT NULL,
    email        VARCHAR(256) NOT NULL UNIQUE,
    password     VARCHAR(256) NOT NULL,
    clearance    VARCHAR(64)  NOT NULL DEFAULT 'operator',
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);