-- Simple explanation: This file adds pretend numbers and a super-serious rule so you can
-- test “send a text when it’s really bad” without messing up your other demo data.
--
-- Demo seed: CRITICAL threshold + aggregated reading that breaches it (Twilio SMS test).
-- Run after migrations. Safe to re-run: refreshes aggregation sample; threshold insert is conditional.

INSERT INTO public.thresholds (zone, metric, condition, threshold_value, severity, is_active)
SELECT 'demo_zone', 'pm25', 'gt', 50.0, 'critical', TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM public.thresholds t
    WHERE t.zone = 'demo_zone' AND t.metric = 'pm25' AND t.is_active = TRUE
);

INSERT INTO public.aggregated_data (zone, metric, value, window_end)
VALUES ('demo_zone', 'pm25', 99.0, now());

-- Optional: clear active demo alert so you can re-trigger SMS after resolving/testing
-- DELETE FROM public.alerts
-- WHERE zone = 'demo_zone' AND metric = 'pm25' AND status = 'active';
