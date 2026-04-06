-- Simple explanation: This file creates the “rule book” table—lines in the sand per room
-- and measurement. When real numbers cross those lines, the system can raise an alert.
--
-- Migration: 003_create_thresholds
-- Rule definitions for the alerting engine (zone + metric + condition + limit).

CREATE TABLE IF NOT EXISTS public.thresholds (
    id BIGSERIAL PRIMARY KEY,
    zone TEXT NOT NULL,
    metric TEXT NOT NULL,
    condition TEXT NOT NULL,
    threshold_value DOUBLE PRECISION NOT NULL,
    severity TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT thresholds_condition_check CHECK (condition IN ('gt', 'gte', 'lt', 'lte', 'eq')),
    CONSTRAINT thresholds_severity_check CHECK (severity IN ('low', 'medium', 'high', 'critical'))
);

CREATE INDEX IF NOT EXISTS idx_thresholds_active ON public.thresholds (is_active)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_thresholds_zone_metric_active
    ON public.thresholds (zone, metric)
    WHERE is_active = TRUE;
