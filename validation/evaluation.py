"""
Evaluation Metrics and Anomaly Detection Engine
Independently scans database for compliance violations, benchmarks against isolated ground truth,
and computes all 12 mandatory evaluation metrics with zero-division safety.
"""

from datetime import datetime
from typing import Dict, Any, List, Set, Tuple
from sqlalchemy.orm import Session
from database.models import (
    Asset, CalibrationEvent, Certificate, WorkOrder,
    ProductionUse, CorrectiveAction, ImpactAssessment,
    CalibrationExtension, CalibrationPlan
)
from generator.ground_truth import load_ground_truth

def detect_anomalies_independently(db: Session, as_of_date: datetime) -> List[Dict[str, Any]]:
    """
    Independent Anomaly Detection Engine.
    Scans database records using pure business rules (ZERO access to ground_truth.csv):
    1. Due date inconsistent with plan interval
    2. Expired instrument used without approved exception
    3. Certificate referring to another asset
    4. Failed calibration not followed by an impact assessment
    """
    detected = []

    # Rule 1: Due Date Inconsistency with Calibration Plan
    plans = {p.plan_id: p for p in db.query(CalibrationPlan).all()}
    assets = db.query(Asset).filter(Asset.last_calibration_date.isnot(None), Asset.next_due_date.isnot(None)).all()
    for a in assets:
        plan = plans.get(a.plan_id)
        if plan:
            expected_due = a.last_calibration_date.date()
            diff_days = (a.next_due_date.date() - expected_due).days
            # If difference deviates from plan interval by more than 1 day
            if abs(diff_days - plan.interval_days) > 1:
                detected.append({
                    "issue_type": "INCONSISTENT_DUE_DATE",
                    "affected_entity_id": a.asset_id,
                    "entity_type": "Asset",
                    "detected_decision": "FLAG_INCONSISTENCY",
                    "reason": f"Due date interval is {diff_days} days, expected {plan.interval_days} days."
                })

    # Rule 2: Expired instrument used without approved exception
    # Check production uses where asset was overdue and no active extension existed, but decision was ALLOWED
    active_extensions = {
        ext.asset_id: ext for ext in db.query(CalibrationExtension).filter(CalibrationExtension.status == "ACTIVE").all()
    }
    prod_uses = db.query(ProductionUse).all()
    for u in prod_uses:
        asset = db.query(Asset).filter(Asset.asset_id == u.asset_id).first()
        if asset and asset.next_due_date:
            if u.usage_timestamp > asset.next_due_date:
                # Check extension
                ext = active_extensions.get(u.asset_id)
                has_valid_ext = (ext and ext.extended_due_date >= u.usage_timestamp)
                if not has_valid_ext and u.decision == "ALLOWED":
                    detected.append({
                        "issue_type": "EXPIRED_INSTRUMENT_USAGE",
                        "affected_entity_id": u.usage_id,
                        "entity_type": "ProductionUse",
                        "detected_decision": "BLOCKED",
                        "reason": f"Usage was ALLOWED but instrument expired on {asset.next_due_date.strftime('%Y-%m-%d')} with no approved extension."
                    })

    # Rule 3: Certificate referring to another asset
    cal_asset_map = {c.calibration_id: c.asset_id for c in db.query(CalibrationEvent).all()}
    certificates = db.query(Certificate).all()
    for cert in certificates:
        cal_asset = cal_asset_map.get(cert.calibration_id)
        if cal_asset and cert.asset_id != cal_asset:
            detected.append({
                "issue_type": "CERTIFICATE_ASSET_MISMATCH",
                "affected_entity_id": cert.certificate_id,
                "entity_type": "Certificate",
                "detected_decision": "FLAG_MISMATCH",
                "reason": f"Certificate references {cert.asset_id}, but calibration was performed on {cal_asset}."
            })

    # Rule 4: Failed calibration not followed by an impact assessment
    impact_cal_ids = {ia.calibration_id for ia in db.query(ImpactAssessment).all()}
    failed_cals = db.query(CalibrationEvent).filter(CalibrationEvent.result == "FAIL").all()
    for fcal in failed_cals:
        if fcal.calibration_id not in impact_cal_ids:
            detected.append({
                "issue_type": "MISSING_IMPACT_ASSESSMENT",
                "affected_entity_id": fcal.calibration_id,
                "entity_type": "CalibrationEvent",
                "detected_decision": "FLAG_MISSING_ASSESSMENT",
                "reason": f"Calibration failure {fcal.calibration_id} has no linked Impact Assessment record."
            })

    return detected

def evaluate_metrics(db: Session, as_of_date: datetime) -> Dict[str, Any]:
    """
    Compute all 12 required metrics with exact definitions and zero-division handling.
    """
    # 1. Calibration Compliance Rate & 2. Overdue Instrument Percentage
    active_assets = db.query(Asset).filter(Asset.status == "ACTIVE").all()
    total_active = len(active_assets)

    active_ext_ids = {
        ext.asset_id for ext in db.query(CalibrationExtension).filter(
            CalibrationExtension.status == "ACTIVE",
            CalibrationExtension.extended_due_date >= as_of_date
        ).all()
    }

    overdue_count = 0
    compliant_count = 0
    for a in active_assets:
        if a.next_due_date and a.next_due_date < as_of_date:
            if a.asset_id in active_ext_ids:
                compliant_count += 1
            else:
                overdue_count += 1
        else:
            compliant_count += 1

    compliance_rate = round((compliant_count / total_active * 100.0) if total_active > 0 else 100.0, 2)
    overdue_percentage = round((overdue_count / total_active * 100.0) if total_active > 0 else 0.0, 2)

    # 3. Failed Calibration Rate
    total_cals = db.query(CalibrationEvent).count()
    failed_cals = db.query(CalibrationEvent).filter(CalibrationEvent.result == "FAIL").count()
    failed_cal_rate = round((failed_cals / total_cals * 100.0) if total_cals > 0 else 0.0, 2)

    # 4. Certificate Completeness Rate
    passed_cals = db.query(CalibrationEvent).filter(CalibrationEvent.result == "PASS").count()
    valid_certs = db.query(Certificate).filter(Certificate.verification_status == "VALID").count()
    cert_completeness_rate = round((min(valid_certs, passed_cals) / passed_cals * 100.0) if passed_cals > 0 else 100.0, 2)

    # 5. Prohibited Usage Count & 6. Unauthorized Usage Rate
    total_uses = db.query(ProductionUse).count()
    blocked_uses = db.query(ProductionUse).filter(ProductionUse.decision == "BLOCKED").count()
    # Also check if any allowed usages were unauthorized anomalies
    detected_anomalies = detect_anomalies_independently(db, as_of_date)
    unauthorized_bypasses = sum(1 for d in detected_anomalies if d["issue_type"] == "EXPIRED_INSTRUMENT_USAGE")
    prohibited_usage_count = blocked_uses + unauthorized_bypasses
    unauthorized_usage_rate = round((prohibited_usage_count / total_uses * 100.0) if total_uses > 0 else 0.0, 2)

    # 7. Mean Time to Repair (MTTR)
    repair_orders = (
        db.query(WorkOrder)
        .filter(
            WorkOrder.status == "COMPLETED",
            WorkOrder.order_type.in_(["FAILED_CALIBRATION", "CORRECTIVE_MAINTENANCE"]),
            WorkOrder.completion_date.isnot(None)
        )
        .all()
    )
    durations = [
        (wo.completion_date - wo.creation_date).total_seconds() / 3600.0
        for wo in repair_orders
        if wo.completion_date >= wo.creation_date
    ]
    mttr_hours = round(sum(durations) / len(durations) if durations else 0.0, 2)

    # 8. Total Downtime
    total_downtime = round(sum(wo.downtime_hours for wo in db.query(WorkOrder).all()), 2)

    # 9. Corrective Action Closure Rate
    total_capas = db.query(CorrectiveAction).count()
    closed_capas = db.query(CorrectiveAction).filter(CorrectiveAction.status == "CLOSED").count()
    capa_closure_rate = round((closed_capas / total_capas * 100.0) if total_capas > 0 else 0.0, 2)

    # 10, 11, 12: Anomaly Detection Precision, Recall, F1
    gt_records = load_ground_truth()
    gt_keys = {(r["issue_type"], r["affected_entity_id"]) for r in gt_records}
    det_keys = {(d["issue_type"], d["affected_entity_id"]) for d in detected_anomalies}

    tp = len(gt_keys.intersection(det_keys))
    fp = len(det_keys - gt_keys)
    fn = len(gt_keys - det_keys)

    precision = round((tp / (tp + fp)) if (tp + fp) > 0 else 1.0, 4)
    recall = round((tp / (tp + fn)) if (tp + fn) > 0 else 1.0, 4)
    f1 = round((2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0, 4)

    return {
        "calibration_compliance_rate": compliance_rate,
        "overdue_instrument_percentage": overdue_percentage,
        "failed_calibration_rate": failed_cal_rate,
        "certificate_completeness_rate": cert_completeness_rate,
        "prohibited_usage_count": prohibited_usage_count,
        "unauthorized_usage_rate": unauthorized_usage_rate,
        "mean_time_to_repair_hours": mttr_hours,
        "total_downtime_hours": total_downtime,
        "corrective_action_closure_rate": capa_closure_rate,
        "anomaly_detection_precision": precision,
        "anomaly_detection_recall": recall,
        "anomaly_detection_f1_score": f1,
        "confusion_matrix": {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "ground_truth_total": len(gt_keys),
            "detected_total": len(det_keys)
        },
        "detected_anomalies": detected_anomalies
    }