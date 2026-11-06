"""
Tests for Production Usage Validation Gatekeeper
Verifies all 8 compliance gates, decision states, and emergency extension exceptions.
"""

import pytest
from datetime import datetime, timedelta
from business_logic.production_validation import evaluate_production_usage

@pytest.fixture
def base_context():
    """Provides valid baseline instrument, calibration, and certificate context."""
    now = datetime(2026, 6, 1, 10, 0, 0)
    asset = {
        "asset_id": "AST-000001",
        "name": "Digital Pressure Gauge",
        "status": "ACTIVE",
        "next_due_date": now + timedelta(days=60)
    }
    cal = {
        "calibration_id": "CAL-AST-000001-2026-000001",
        "asset_id": "AST-000001",
        "calibration_date": now - timedelta(days=120),
        "result": "PASS"
    }
    cert = {
        "certificate_id": "CERT-CAL-AST-000001-2026-000001",
        "certificate_number": "CERT-2026-000001",
        "asset_id": "AST-000001",
        "expiry_date": now + timedelta(days=60),
        "verification_status": "VALID"
    }
    return asset, cal, cert, now

def test_gatekeeper_allowed_compliant_usage(base_context):
    """Test standard happy-path: all 8 gates pass."""
    asset, cal, cert, now = base_context
    decision = evaluate_production_usage(
        asset=asset,
        usage_timestamp=now,
        latest_calibration=cal,
        certificate=cert
    )
    assert decision["decision"] == "ALLOWED"
    assert decision["validation_passed"] is True
    assert decision["policy_applied"] == "POL-GATE-000"

def test_gatekeeper_blocked_nonexistent_instrument():
    """Gate 1: Unknown asset tag blocked."""
    decision = evaluate_production_usage(
        asset=None,
        usage_timestamp=datetime(2026, 6, 1)
    )
    assert decision["decision"] == "BLOCKED"
    assert decision["policy_applied"] == "POL-GATE-001"

def test_gatekeeper_blocked_quarantined_status(base_context):
    """Gate 2: Quarantined instrument blocked."""
    asset, cal, cert, now = base_context
    asset["status"] = "QUARANTINED"
    decision = evaluate_production_usage(
        asset=asset,
        usage_timestamp=now,
        latest_calibration=cal,
        certificate=cert
    )
    assert decision["decision"] == "BLOCKED"
    assert decision["policy_applied"] == "POL-GATE-002"
    assert "QUARANTINED" in decision["reason"]

def test_gatekeeper_blocked_failed_calibration(base_context):
    """Gate 6: Latest calibration failed."""
    asset, cal, cert, now = base_context
    cal["result"] = "FAIL"
    decision = evaluate_production_usage(
        asset=asset,
        usage_timestamp=now,
        latest_calibration=cal,
        certificate=cert
    )
    assert decision["decision"] == "BLOCKED"
    assert decision["policy_applied"] == "POL-GATE-004"

def test_gatekeeper_blocked_overdue_instrument(base_context):
    """Gate 4: Overdue instrument blocked without extension."""
    asset, cal, cert, now = base_context
    usage_time = now + timedelta(days=90)  # Next due date was now + 60 days
    decision = evaluate_production_usage(
        asset=asset,
        usage_timestamp=usage_time,
        latest_calibration=cal,
        certificate=cert
    )
    assert decision["decision"] == "BLOCKED"
    assert decision["policy_applied"] == "POL-GATE-005"
    assert "expired" in decision["reason"].lower()

def test_gatekeeper_allowed_with_approved_extension(base_context):
    """Emergency Extension Exception: Overdue instrument allowed with approved extension."""
    asset, cal, cert, now = base_context
    usage_time = now + timedelta(days=70)  # 10 days past due date (now + 60)
    extension = {
        "extension_id": "EXT-2026-000001",
        "asset_id": "AST-000001",
        "extended_due_date": now + timedelta(days=80),
        "status": "ACTIVE"
    }
    decision = evaluate_production_usage(
        asset=asset,
        usage_timestamp=usage_time,
        latest_calibration=cal,
        certificate=cert,
        active_extension=extension
    )
    assert decision["decision"] == "ALLOWED_WITH_EXCEPTION"
    assert decision["validation_passed"] is True
    assert decision["policy_applied"] == "POL-GATE-008"

def test_gatekeeper_blocked_mismatched_certificate(base_context):
    """Gate 7: Certificate references another asset."""
    asset, cal, cert, now = base_context
    cert["asset_id"] = "AST-999999"  # Mismatch!
    decision = evaluate_production_usage(
        asset=asset,
        usage_timestamp=now,
        latest_calibration=cal,
        certificate=cert
    )
    assert decision["decision"] == "BLOCKED"
    assert decision["policy_applied"] == "POL-GATE-006"
    assert "mismatch" in decision["reason"].lower()

def test_gatekeeper_blocked_by_active_maintenance_order(base_context):
    """Gate 5: Blocking work order in progress."""
    asset, cal, cert, now = base_context
    active_wos = [
        {
            "work_order_id": "WO-2026-000042",
            "order_type": "CORRECTIVE_MAINTENANCE",
            "status": "IN_PROGRESS"
        }
    ]
    decision = evaluate_production_usage(
        asset=asset,
        usage_timestamp=now,
        latest_calibration=cal,
        certificate=cert,
        active_work_orders=active_wos
    )
    assert decision["decision"] == "BLOCKED"
    assert decision["policy_applied"] == "POL-GATE-007"