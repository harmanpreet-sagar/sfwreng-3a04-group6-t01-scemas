-- Simple explanation: This file creates the database “notebook” where each alert is
-- saved—like a flag that says something went wrong in a zone, how serious it is,
-- and whether someone already handled it.
--
-- Migration: 001_create_alerts
-- Creates the alerts table for operational monitoring + history.

CREATE TABLE IF NOT EXISTS public.alerts (
    id BIGSERIAL PRIMARY KEY,
    zone TEXT NOT NULL,
    metric TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    observed_value DOUBLE PRECISION NULL,
    threshold_value DOUBLE PRECISION NULL,
    threshold_id BIGINT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    acknowledged_at TIMESTAMPTZ NULL,
    resolved_at TIMESTAMPTZ NULL,
    CONSTRAINT alerts_status_check CHECK (status IN ('active', 'acknowledged', 'resolved')),
    CONSTRAINT alerts_severity_check CHECK (severity IN ('low', 'medium', 'high', 'critical'))
);

-- Basic filtering / sorting indexes
CREATE INDEX IF NOT EXISTS idx_alerts_status ON public.alerts (status);
CREATE INDEX IF NOT EXISTS idx_alerts_zone ON public.alerts (zone);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON public.alerts (severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON public.alerts (created_at);

-- Fast lookups for "active alert already exists for zone + metric"
CREATE UNIQUE INDEX IF NOT EXISTS uq_alerts_active_zone_metric
    ON public.alerts (zone, metric)
    WHERE status = 'active';

-- Common future access pattern: list active alerts by zone/metric quickly
CREATE INDEX IF NOT EXISTS idx_alerts_zone_metric_status
    ON public.alerts (zone, metric, status);

