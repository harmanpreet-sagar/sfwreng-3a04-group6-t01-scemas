"""Assemble public-safe zone summaries from aggregated_data (+ alert severity rollup)."""

from __future__ import annotations

from collections import defaultdict

from app.models.alert import AlertSeverity
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
