-- Migration: 004_create_aggregated_data
-- Latest aggregated environmental readings per zone/metric (written by aggregation subsystem).
-- Evaluator uses the row with the greatest window_end for each (zone, metric).

CREATE TABLE IF NOT EXISTS public.aggregated_data (
    id BIGSERIAL PRIMARY KEY,
    zone TEXT NOT NULL,
    metric TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_aggregated_data_zone_metric_window
    ON public.aggregated_data (zone, metric, window_end DESC);
