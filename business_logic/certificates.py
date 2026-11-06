"""
Certificate Verification and Reconciliation Business Logic
Reconciles certificates with assets and calibration records; detects mismatches, expirations, and missing certificates.
"""

from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

def validate_certificate_linkage(
    certificate: Dict[str, Any],
    calibration_event: Dict[str, Any],
    as_of_date: Optional[datetime] = None
) -> Tuple[bool, str, List[str]]:
    """
    Validate that a certificate properly matches its calibration event and asset.
    Returns: (is_valid, status, issues)
    """
    issues = []
    cert_id = certificate.get("certificate_id")
    cert_asset_id = certificate.get("asset_id")
    cal_asset_id = calibration_event.get("asset_id")
    cal_id = calibration_event.get("calibration_id")
    
    # 1. Reconciliation check
    if cert_asset_id != cal_asset_id:
        issues.append(
            f"Asset mismatch: certificate references {cert_asset_id}, but calibration was for {cal_asset_id}"
        )
        return False, "MISMATCHED", issues

    if certificate.get("calibration_id") != cal_id:
        issues.append(
            f"Calibration mismatch: certificate references {certificate.get('calibration_id')}, expected {cal_id}"
        )
        return False, "MISMATCHED", issues

    # 2. Expiry check
    if as_of_date:
        if isinstance(as_of_date, str):
            as_of_date = datetime.fromisoformat(as_of_date)
        exp_date = certificate.get("expiry_date")
        if isinstance(exp_date, str):
            exp_date = datetime.fromisoformat(exp_date)
        if exp_date and as_of_date > exp_date:
            issues.append(f"Certificate expired on {exp_date.isoformat()}")
            return False, "EXPIRED", issues

    # 3. Status check
    current_status = certificate.get("verification_status", "VALID")
    if current_status == "REVOKED":
        issues.append("Certificate has been formally revoked.")
        return False, "REVOKED", issues

    return True, "VALID", []

def detect_certificate_anomalies(
    certificates: List[Dict[str, Any]],
    calibration_events: List[Dict[str, Any]],
    as_of_date: Optional[datetime] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Systematically scan certificate database for:
    - Mismatched certificates (linked to wrong asset)
    - Expired certificates
    - Missing certificates for passed calibrations
    """
    cal_map = {c["calibration_id"]: c for c in calibration_events}
    cert_cal_ids = {c["calibration_id"] for c in certificates}

    mismatches = []
    expired = []
    missing = []

    for cert in certificates:
        cal = cal_map.get(cert.get("calibration_id"))
        if cal:
            is_valid, status, issues = validate_certificate_linkage(cert, cal, as_of_date)
            if status == "MISMATCHED":
                mismatches.append({"certificate": cert, "issues": issues})
            elif status == "EXPIRED":
                expired.append({"certificate": cert, "issues": issues})

    for cal in calibration_events:
        # If calibration passed and mandatory cert is required, check if cert exists
        if cal.get("result") == "PASS" and cal.get("calibration_id") not in cert_cal_ids:
            missing.append(cal)

    return {
        "mismatched": mismatches,
        "expired": expired,
        "missing": missing
    }