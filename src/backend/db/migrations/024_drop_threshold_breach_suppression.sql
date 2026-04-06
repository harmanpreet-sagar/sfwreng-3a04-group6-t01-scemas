-- Removes post-resolve suppression (reverted feature). Safe if the table was never created.
DROP TABLE IF EXISTS public.threshold_breach_suppression;
