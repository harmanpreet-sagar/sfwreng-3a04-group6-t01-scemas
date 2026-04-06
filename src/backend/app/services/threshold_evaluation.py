"""
Periodic threshold evaluation against latest aggregated values.

Calls `AlertService.create_alert` on breach; duplicate active alerts are prevented there
and via the partial unique index on `alerts`.

Simple explanation: The checker that compares latest averaged numbers to the rules; if a
rule is broken, it tells the alert boss to raise a flag.
"""

from __future__ import annotations

import logging
import math

import psycopg.errors

from app.shared.alert import AlertCreate
from app.shared.enums import AlertSeverity
from app.services import aggregated_data_repository, threshold_repository
from app.services.alert_service import AlertService
from app.shared.db import get_supabase_db_url

logger = logging.getLogger(__name__)

_warned_thresholds_missing = False
_warned_aggregated_or_alerts_missing = False


def is_threshold_breached(condition: str, observed: float, limit_value: float) -> bool:
    """Evaluate one rule; `condition` matches `public.thresholds.condition`."""
    if condition == "gt":
        return observed > limit_value
    if condition == "gte":
        return observed >= limit_value
    if condition == "lt":
        return observed < limit_value
    if condition == "lte":
        return observed <= limit_value
    if condition == "eq":
        return math.isclose(observed, limit_value, rel_tol=1e-9, abs_tol=1e-9)
    logger.warning("Unknown threshold condition %r; treating as not breached", condition)
    return False


def run_threshold_evaluation_cycle() -> None:
    """
    One pass: active thresholds × latest aggregated value per zone/metric; create alerts on breach.
    Safe to call on a timer; logs and returns on missing DB URL, missing tables, or per-rule errors.
    """
    global _warned_thresholds_missing, _warned_aggregated_or_alerts_missing

    if not get_supabase_db_url():
        return

    try:
        thresholds = threshold_repository.list_active_thresholds()
    except psycopg.errors.UndefinedTable:
        if not _warned_thresholds_missing:
            logger.warning(
                "Table public.thresholds not found; apply db/migrations/003_create_thresholds.sql"
            )
            _warned_thresholds_missing = True
        return
    except Exception:
        logger.exception("Failed to load active thresholds")
        return

    for rule in thresholds:
        try:
            observed = aggregated_data_repository.fetch_latest_aggregated_value(
                rule.zone, rule.metric
            )
            if observed is None:
                logger.debug(
                    "No aggregated_data for zone=%r metric=%r; skipping",
                    rule.zone,
                    rule.metric,
                )
                continue

            if not is_threshold_breached(rule.condition, observed, rule.threshold_value):
                continue

            try:
                severity = AlertSeverity(rule.severity)
            except ValueError:
                logger.warning(
                    "Invalid severity %r on threshold id=%s; skipping",
                    rule.severity,
                    rule.id,
                )
                continue

            message = (
                f"{rule.metric} in zone {rule.zone} breached threshold "
                f"({rule.condition} {rule.threshold_value}); observed {observed}"
            )
            payload = AlertCreate(
                zone=rule.zone,
                metric=rule.metric,
                severity=severity,
                message=message,
                observed_value=observed,
                threshold_value=rule.threshold_value,
                threshold_id=rule.id,
            )
            outcome = AlertService.create_alert(payload)
            if outcome.created:
                logger.info(
                    "Alert created for threshold id=%s zone=%r metric=%r",
                    rule.id,
                    rule.zone,
                    rule.metric,
                )
            elif outcome.skipped_duplicate_active:
                logger.debug(
                    "Skipped alert for threshold id=%s (active alert already exists)",
                    rule.id,
                )
        except psycopg.errors.UndefinedTable:
            if not _warned_aggregated_or_alerts_missing:
                logger.warning(
                    "aggregated_data and/or alerts table missing; apply migrations "
                    "001_create_alerts.sql and 004_create_aggregated_data.sql"
                )
                _warned_aggregated_or_alerts_missing = True
            return
        except Exception:
            logger.exception(
                "Threshold evaluation failed for threshold id=%s zone=%r metric=%r",
                rule.id,
                rule.zone,
                rule.metric,
            )
