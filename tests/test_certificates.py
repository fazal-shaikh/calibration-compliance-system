"""
Tests for Certificate Reconciliation and Validation Logic
"""

import pytest
from datetime import datetime, timedelta
from business_logic.certificates import validate_certificate_linkage, detect_certificate_anomalies

def test_certificate_validation_valid():
    """Verify valid certificate properly links to calibration and asset."""
    cal = {"calibration_id": "CAL-001", "asset_id": "AST-001", "result": "PASS"}
    cert = {
        "certificate_id": "CERT-001",
        "calibration_id": "CAL-001",
        "asset_id": "AST-001",
        "expiry_date": datetime(2026, 12, 31),
        "verification_status": "VALID"
    }
    is_valid, status, issues = validate_certificate_linkage(cert, cal, datetime(2026, 6, 1))
    assert is_valid is True
    assert status == "VALID"
    assert len(issues) == 0

def test_certificate_validation_mismatch():
    """Verify detection when certificate references a different asset than calibration."""
    cal = {"calibration_id": "CAL-001", "asset_id": "AST-001"}
    cert = {
        "certificate_id": "CERT-001",
        "calibration_id": "CAL-001",
        "asset_id": "AST-002",  # Mismatch!
        "expiry_date": datetime(2026, 12, 31),
        "verification_status": "VALID"
    }
    is_valid, status, issues = validate_certificate_linkage(cert, cal)
    assert is_valid is False
    assert status == "MISMATCHED"
    assert any("Asset mismatch" in iss for iss in issues)

def test_certificate_validation_expired():
    """Verify detection when certificate has expired."""
    cal = {"calibration_id": "CAL-001", "asset_id": "AST-001"}
    cert = {
        "certificate_id": "CERT-001",
        "calibration_id": "CAL-001",
        "asset_id": "AST-001",
        "expiry_date": datetime(2026, 5, 1),
        "verification_status": "VALID"
    }
    is_valid, status, issues = validate_certificate_linkage(cert, cal, as_of_date=datetime(2026, 6, 1))
    assert is_valid is False
    assert status == "EXPIRED"

def test_detect_missing_certificates():
    """Verify detection of passed calibrations lacking issued certificates."""
    calibrations = [
        {"calibration_id": "CAL-001", "asset_id": "AST-001", "result": "PASS"},
        {"calibration_id": "CAL-002", "asset_id": "AST-002", "result": "PASS"},
        {"calibration_id": "CAL-003", "asset_id": "AST-003", "result": "FAIL"}
    ]
    certificates = [
        {"certificate_id": "CERT-001", "calibration_id": "CAL-001", "asset_id": "AST-001", "verification_status": "VALID"}
    ]
    res = detect_certificate_anomalies(certificates, calibrations)
    assert len(res["missing"]) == 1
    assert res["missing"][0]["calibration_id"] == "CAL-002"