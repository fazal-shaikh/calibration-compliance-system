"""
Compliance Alerts Generation and Lifecycle Engine
Monitors compliance indicators and generates prioritized operational alerts.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

SEVERITY_MAP = {
    "FAILED_CALIBRATION": "CRITICAL",
    "UNAUTHORIZED_USAGE": "CRITICAL",
    "OVERDUE_CALIBRATION": "HIGH",
    "MISSING_IMPACT_ASSESSMENT": "HIGH",
    "EXPIRED_CERTIFICATE": "HIGH",
    "MISSING_CERTIFICATE": "MEDIUM",
    "EXTENSION_EXPIRY": "MEDIUM",
    "UPCOMING_CALIBRATION": "LOW"
}

def create_alert(
    alert_id: str,
    alert_type: str,
    message: str,
    asset_id: Optional[str] = None,
    created_at: Optional[datetime] = None,
    severity: Optional[str] = None
) -> Dict[str, Any]:
    """Factory function for generating alerts with standardized severity."""
    now = created_at or datetime.utcnow()
    sev = severity or SEVERITY_MAP.get(alert_type, "MEDIUM")

    return {
        "alert_id": alert_id,
        "asset_id": asset_id,
        "alert_type": alert_type,
        "severity": sev,
        "message": message,
        "status": "ACTIVE",
        "created_at": now,
        "acknowledged_at": None,
        "resolved_at": None
    }

def acknowledge_alert(alert: Dict[str, Any], ack_date: datetime) -> Dict[str, Any]:
    """Acknowledge active alert."""
    alert["status"] = "ACKNOWLEDGED"
    alert["acknowledged_at"] = ack_date
    return alert

def resolve_alert(alert: Dict[str, Any], res_date: datetime) -> Dict[str, Any]:
    """Resolve alert."""
    alert["status"] = "RESOLVED"
    alert["resolved_at"] = res_date
    return alert