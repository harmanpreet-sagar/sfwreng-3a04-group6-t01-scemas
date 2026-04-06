"""Assemble public-safe zone summaries from aggregated_data (+ alert severity rollup).

Simple explanation: Builds those public zone summaries by mixing latest averaged readings
with “how bad are open alerts in this zone?” so signs or kiosks can show a simple status.
"""

from __future__ import annotations

from collections import defaultdict

from app.shared.enums import AlertSeverity
from app.models.public_zone import (
    PublicZoneMetricReading,
    PublicZoneOperationalStatus,
    PublicZoneSummary,
    PublicZonesListResponse,
)
from app.services import aggregated_data_repository, alert_repository


def list_public_zones() -> PublicZonesListResponse:
    rows = aggregated_data_repository.fetch_latest_row_per_zone_metric()
    worst_severity_by_zone = alert_repository.fetch_worst_active_severity_per_zone()

    by_zone: dict[str, list[PublicZoneMetricReading]] = defaultdict(list)
    for row in rows:
        zone = str(row["zone"])
        by_zone[zone].append(
            PublicZoneMetricReading(
                metric=str(row["metric"]),
                value=float(row["value"]),
                window_end=row["window_end"],
            )
        )

    summaries: list[PublicZoneSummary] = []
    for zone in sorted(by_zone.keys()):
        metrics = sorted(by_zone[zone], key=lambda m: m.metric)
        updated_at = max(m.window_end for m in metrics)
        sev_str = worst_severity_by_zone.get(zone)
        if sev_str is not None:
            status = PublicZoneOperationalStatus.alerting
            highest = AlertSeverity(sev_str)
        else:
            status = PublicZoneOperationalStatus.normal
            highest = None
        summaries.append(
            PublicZoneSummary(
                zone=zone,
                metrics=metrics,
                updated_at=updated_at,
                status=status,
                active_alert_highest_severity=highest,
            )
        )

    return PublicZonesListResponse(zones=summaries, total=len(summaries))


def get_public_zone(zone: str) -> PublicZoneSummary | None:
    """
    One zone’s public summary, or None if there is no aggregated_data for that zone.
    """
    rows = aggregated_data_repository.fetch_latest_row_per_metric_for_zone(zone)
    if not rows:
        return None

    metrics = sorted(
        (
            PublicZoneMetricReading(
                metric=str(r["metric"]),
                value=float(r["value"]),
                window_end=r["window_end"],
            )
            for r in rows
        ),
        key=lambda m: m.metric,
    )
    updated_at = max(m.window_end for m in metrics)
    sev_str = alert_repository.fetch_worst_active_severity_for_zone(zone)
    if sev_str is not None:
        status = PublicZoneOperationalStatus.alerting
        highest = AlertSeverity(sev_str)
    else:
        status = PublicZoneOperationalStatus.normal
        highest = None

    return PublicZoneSummary(
        zone=str(rows[0]["zone"]),
        metrics=metrics,
        updated_at=updated_at,
        status=status,
        active_alert_highest_severity=highest,
    )
