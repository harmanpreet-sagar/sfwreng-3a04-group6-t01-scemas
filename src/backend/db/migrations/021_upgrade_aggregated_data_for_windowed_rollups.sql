-- Migration: 021_upgrade_aggregated_data_for_windowed_rollups
-- Upgrade the original aggregated_data table so it can store:
--   - 5-minute averages
--   - 5-minute maxima
--   - hourly maxima

ALTER TABLE public.aggregated_data
    ADD COLUMN IF NOT EXISTS aggregation_window TEXT,
    ADD COLUMN IF NOT EXISTS aggregation_type TEXT,
    ADD COLUMN IF NOT EXISTS window_start TIMESTAMPTZ;

-- Backfill existing rows so older data remains usable after the upgrade.
UPDATE public.aggregated_data
SET aggregation_window = COALESCE(aggregation_window, '5m'),
    aggregation_type = COALESCE(aggregation_type, 'avg'),
    window_start = COALESCE(window_start, window_end - interval '5 minutes');

ALTER TABLE public.aggregated_data
    ALTER COLUMN aggregation_window SET NOT NULL,
    ALTER COLUMN aggregation_type SET NOT NULL,
    ALTER COLUMN window_start SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'aggregated_data_window_check'
          AND conrelid = 'public.aggregated_data'::regclass
    ) THEN
        ALTER TABLE public.aggregated_data
            ADD CONSTRAINT aggregated_data_window_check
            CHECK (aggregation_window IN ('5m', '1h'));
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'aggregated_data_type_check'
          AND conrelid = 'public.aggregated_data'::regclass
    ) THEN
        ALTER TABLE public.aggregated_data
            ADD CONSTRAINT aggregated_data_type_check
            CHECK (aggregation_type IN ('avg', 'max'));
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'aggregated_data_window_order_check'
          AND conrelid = 'public.aggregated_data'::regclass
    ) THEN
        ALTER TABLE public.aggregated_data
            ADD CONSTRAINT aggregated_data_window_order_check
            CHECK (window_start < window_end);
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_aggregated_data_bucket
    ON public.aggregated_data (
        zone, metric, aggregation_window, aggregation_type, window_end
    );

DROP INDEX IF EXISTS idx_aggregated_data_zone_metric_window;

CREATE INDEX IF NOT EXISTS idx_aggregated_data_zone_metric_window_type_end
    ON public.aggregated_data (
        zone,
        metric,
        aggregation_window,
        aggregation_type,
        window_end DESC
    );

CREATE INDEX IF NOT EXISTS idx_aggregated_data_window_type_end
    ON public.aggregated_data (aggregation_window, aggregation_type, window_end DESC);
