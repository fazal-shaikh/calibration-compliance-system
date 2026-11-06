"""
Lifecycle Validation Engine
Verifies that instrument operational state transitions, maintenance workflows,
and calibration resolution lifecycles conform to business policies.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from database.models import Asset, CalibrationEvent, WorkOrder, CorrectiveAction

def validate_lifecycle_transitions(db: Session) -> Dict[str, Any]:
    """
    Validate that operational states reflect appropriate lifecycle transitions.
    """
    violations = []
    checks_performed = 0

    # 1. Check failed calibrations have quarantined status or active investigation
    failed_cals = db.query(CalibrationEvent).filter(CalibrationEvent.result == "FAIL").all()
    for cal in failed_cals:
        checks_performed += 1
        asset = db.query(Asset).filter(Asset.asset_id == cal.asset_id).first()
        # Asset must have been quarantined or transitioned to out of service / in calibration
        if asset and asset.status == "ACTIVE":
            # If active, must have a subsequent passed calibration
            newer_pass = (
                db.query(CalibrationEvent)
                .filter(
                    CalibrationEvent.asset_id == asset.asset_id,
                    CalibrationEvent.calibration_date > cal.calibration_date,
                    CalibrationEvent.result == "PASS"
                )
                .first()
            )
            if not newer_pass:
                violations.append(
                    f"Lifecycle violation: Asset {asset.asset_id} remains ACTIVE despite failing calibration {cal.calibration_id} with no subsequent PASS."
                )

    # 2. Check completed work orders have valid completion dates and positive or zero downtime
    work_orders = db.query(WorkOrder).all()
    for wo in work_orders:
        checks_performed += 1
        if wo.status == "COMPLETED":
            if not wo.completion_date:
                violations.append(f"Work order {wo.work_order_id} marked COMPLETED but completion_date is NULL.")
            if wo.downtime_hours < 0:
                violations.append(f"Work order {wo.work_order_id} has negative downtime {wo.downtime_hours}.")
        elif wo.status in ["OPEN", "IN_PROGRESS"]:
            if wo.completion_date:
                violations.append(f"Work order {wo.work_order_id} is {wo.status} but has a non-null completion_date.")

    # 3. Check CAPA states
    capas = db.query(CorrectiveAction).all()
    for capa in capas:
        checks_performed += 1
        if capa.status == "CLOSED" and not capa.closed_date:
            violations.append(f"CAPA {capa.corrective_action_id} marked CLOSED but closed_date is NULL.")

    return {
        "checks_performed": checks_performed,
        "violations_count": len(violations),
        "violations": violations
    }