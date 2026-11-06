"""
Production Usage Validation Gatekeeper Engine
Enforces 8-point gate check before permitting shopfloor instrument usage.
Determines ALLOWED, BLOCKED, or ALLOWED_WITH_EXCEPTION verdicts with full policy traceability.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Policy Codes
POL_INSTRUMENT_NOT_FOUND = "POL-GATE-001"
POL_STATUS_PROHIBITED = "POL-GATE-002"
POL_NO_CALIBRATION = "POL-GATE-003"
POL_CALIBRATION_FAILED = "POL-GATE-004"
POL_CALIBRATION_OVERDUE = "POL-GATE-005"
POL_CERTIFICATE_INVALID = "POL-GATE-006"
POL_BLOCKING_WORK_ORDER = "POL-GATE-007"
POL_EMERGENCY_EXTENSION = "POL-GATE-008"
POL_COMPLIANT_USAGE = "POL-GATE-000"

def evaluate_production_usage(
    asset: Optional[Dict[str, Any]],
    usage_timestamp: datetime,
    latest_calibration: Optional[Dict[str, Any]] = None,
    certificate: Optional[Dict[str, Any]] = None,
    active_work_orders: Optional[List[Dict[str, Any]]] = None,
    active_extension: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evaluate 8-point compliance gate for shopfloor instrument usage.
    Returns dictionary with decision, policy_applied, reason, and validation_passed.
    """
    if isinstance(usage_timestamp, str):
        usage_timestamp = datetime.fromisoformat(usage_timestamp)

    # 1. Instrument existence
    if not asset:
        return {
            "decision": "BLOCKED",
            "policy_applied": POL_INSTRUMENT_NOT_FOUND,
            "reason": "Instrument record does not exist in master registry.",
            "validation_passed": False
        }

    asset_id = asset.get("asset_id")
    status = asset.get("status", "ACTIVE")

    # 2. Operational Status Check & Prohibitions
    if status in ["QUARANTINED", "OUT_OF_SERVICE", "RETIRED"]:
        return {
            "decision": "BLOCKED",
            "policy_applied": POL_STATUS_PROHIBITED,
            "reason": f"Instrument is currently in prohibited status: {status}.",
            "validation_passed": False
        }

    # 3. Latest Applicable Calibration Exists
    if not latest_calibration:
        return {
            "decision": "BLOCKED",
            "policy_applied": POL_NO_CALIBRATION,
            "reason": "No calibration history recorded for this instrument.",
            "validation_passed": False
        }

    # 4. Latest Applicable Calibration Passed
    if latest_calibration.get("result") != "PASS":
        return {
            "decision": "BLOCKED",
            "policy_applied": POL_CALIBRATION_FAILED,
            "reason": f"Latest calibration test {latest_calibration.get('calibration_id')} resulted in FAIL.",
            "validation_passed": False
        }

    # 5. Blocking Maintenance / Work Orders Check
    if active_work_orders:
        blocking_types = {"FAILED_CALIBRATION", "CORRECTIVE_MAINTENANCE", "OVERDUE_CALIBRATION"}
        for wo in active_work_orders:
            if wo.get("status") in ["OPEN", "IN_PROGRESS"] and wo.get("order_type") in blocking_types:
                return {
                    "decision": "BLOCKED",
                    "policy_applied": POL_BLOCKING_WORK_ORDER,
                    "reason": f"Active blocking work order {wo.get('work_order_id')} ({wo.get('order_type')}) in progress.",
                    "validation_passed": False
                }

    # 6. Due Date & Validity Window Check
    next_due_date = asset.get("next_due_date")
    if isinstance(next_due_date, str):
        next_due_date = datetime.fromisoformat(next_due_date)

    is_past_due = False
    if next_due_date and usage_timestamp > next_due_date:
        is_past_due = True

    # Check emergency extension if past due
    if is_past_due:
        if active_extension:
            ext_due = active_extension.get("extended_due_date")
            if isinstance(ext_due, str):
                ext_due = datetime.fromisoformat(ext_due)
            if ext_due >= usage_timestamp:
                return {
                    "decision": "ALLOWED_WITH_EXCEPTION",
                    "policy_applied": POL_EMERGENCY_EXTENSION,
                    "reason": (
                        f"Calibration expired on {next_due_date.isoformat()}, but covered by approved "
                        f"emergency extension {active_extension.get('extension_id')} valid until {ext_due.isoformat()}."
                    ),
                    "validation_passed": True
                }

        return {
            "decision": "BLOCKED",
            "policy_applied": POL_CALIBRATION_OVERDUE,
            "reason": (
                f"Instrument calibration expired on {next_due_date.isoformat() if next_due_date else 'UNKNOWN'}. "
                "No approved emergency extension found."
            ),
            "validation_passed": False
        }

    # 7. Certificate Validity & Asset Reconcile Check
    if certificate:
        # Check asset reconciliation
        if certificate.get("asset_id") != asset_id:
            return {
                "decision": "BLOCKED",
                "policy_applied": POL_CERTIFICATE_INVALID,
                "reason": (
                    f"Certificate {certificate.get('certificate_number')} asset mismatch: "
                    f"assigned to {certificate.get('asset_id')}, attempted use on {asset_id}."
                ),
                "validation_passed": False
            }

        # Check certificate expiry
        cert_expiry = certificate.get("expiry_date")
        if isinstance(cert_expiry, str):
            cert_expiry = datetime.fromisoformat(cert_expiry)
        if cert_expiry and usage_timestamp > cert_expiry:
            return {
                "decision": "BLOCKED",
                "policy_applied": POL_CERTIFICATE_INVALID,
                "reason": f"Calibration certificate expired on {cert_expiry.isoformat()}.",
                "validation_passed": False
            }

        # Check revocation
        if certificate.get("verification_status") in ["REVOKED", "MISMATCHED"]:
            return {
                "decision": "BLOCKED",
                "policy_applied": POL_CERTIFICATE_INVALID,
                "reason": f"Calibration certificate verification status is {certificate.get('verification_status')}.",
                "validation_passed": False
            }

    # 8. All compliance gates passed
    return {
        "decision": "ALLOWED",
        "policy_applied": POL_COMPLIANT_USAGE,
        "reason": "All 8 compliance validation gates passed successfully.",
        "validation_passed": True
    }