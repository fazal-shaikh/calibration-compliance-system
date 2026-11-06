"""
Corrective Actions (CAPA) and Impact Assessment Business Logic
Handles failure workflows, retrospective production batch tracing, risk rating, and dispositioning.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

def trace_affected_production(
    asset_id: str,
    failure_date: datetime,
    last_valid_calibration_date: Optional[datetime],
    production_uses: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Identify and extract all production runs between the last known valid calibration and failure date.
    Returns list of affected uses, unique batch IDs, and total count.
    """
    if isinstance(failure_date, str):
        failure_date = datetime.fromisoformat(failure_date)
    if isinstance(last_valid_calibration_date, str):
        last_valid_calibration_date = datetime.fromisoformat(last_valid_calibration_date)

    affected_uses = []
    affected_batches = set()

    for u in production_uses:
        if u.get("asset_id") == asset_id:
            u_time = u.get("usage_timestamp")
            if isinstance(u_time, str):
                u_time = datetime.fromisoformat(u_time)
            
            # If there was a previous valid calibration, trace from then to failure
            if last_valid_calibration_date:
                in_window = (last_valid_calibration_date <= u_time <= failure_date)
            else:
                in_window = (u_time <= failure_date)

            if in_window:
                affected_uses.append(u)
                if u.get("batch_id"):
                    affected_batches.add(u.get("batch_id"))

    return {
        "asset_id": asset_id,
        "affected_uses": affected_uses,
        "affected_batches": list(affected_batches),
        "affected_usage_events_count": len(affected_uses),
        "affected_batches_count": len(affected_batches)
    }

def create_failure_containment(
    calibration_id: str,
    asset_id: str,
    failure_date: datetime,
    last_valid_calibration_date: Optional[datetime],
    production_uses: List[Dict[str, Any]],
    technician: str = "Lead QA Metrologist"
) -> Dict[str, Any]:
    """
    Executes mandatory failure workflow:
    1. Traces affected batches
    2. Constructs ImpactAssessment
    3. Constructs CorrectiveAction (CAPA)
    """
    trace_res = trace_affected_production(
        asset_id=asset_id,
        failure_date=failure_date,
        last_valid_calibration_date=last_valid_calibration_date,
        production_uses=production_uses
    )

    batch_count = trace_res["affected_batches_count"]
    risk_level = "CRITICAL" if batch_count > 10 else ("HIGH" if batch_count > 0 else "MEDIUM")

    assessment_id = f"IMP-{calibration_id.replace('CAL-', '')}"
    capa_id = f"CAPA-{calibration_id.replace('CAL-', '')}"

    impact_assessment = {
        "assessment_id": assessment_id,
        "calibration_id": calibration_id,
        "asset_id": asset_id,
        "investigation_status": "OPEN",
        "risk_level": risk_level,
        "affected_batches_count": batch_count,
        "affected_usage_events_count": trace_res["affected_usage_events_count"],
        "investigation_summary": (
            f"Retrospective impact analysis identified {batch_count} production batches "
            f"and {trace_res['affected_usage_events_count']} usage events between last valid calibration and failure."
        ),
        "disposition": "Quarantined Pending Batch Review",
        "assessor": technician,
        "assessment_date": failure_date,
        "closed_date": None,
        "created_at": failure_date
    }

    corrective_action = {
        "corrective_action_id": capa_id,
        "calibration_id": calibration_id,
        "asset_id": asset_id,
        "work_order_id": None,
        "status": "OPEN",
        "root_cause": "Pending metallurgical and sensor drift investigation.",
        "containment_action": "Instrument quarantined and locked out in system. Affected batches tagged.",
        "preventive_action": "Tighten calibration frequency interval and assess environmental exposure.",
        "assigned_to": technician,
        "target_date": failure_date,
        "closed_date": None,
        "created_at": failure_date
    }

    return {
        "impact_assessment": impact_assessment,
        "corrective_action": corrective_action,
        "trace_summary": trace_res
    }