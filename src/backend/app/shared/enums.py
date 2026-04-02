"""Shared enums used across all subsystem models."""

from __future__ import annotations

from enum import Enum


class AlertStatus(str, Enum):
    active = "active"
    acknowledged = "acknowledged"
    resolved = "resolved"


class AlertSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class UserRole(str, Enum):
    admin = "ADMIN"
    operator = "OPERATOR"


class ThresholdCondition(str, Enum):
    gt = "gt"
    gte = "gte"
    lt = "lt"
    lte = "lte"
    eq = "eq"


class ValidationStatus(str, Enum):
    valid = "valid"
    invalid = "invalid"
    anomaly = "anomaly"
