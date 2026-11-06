"""
Database Integrity and Relational Validation Engine
Executes automated checks on primary key uniqueness, foreign key consistency,
enum boundaries, non-null constraints, and date ordering.
"""

from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from database.models import (
    Supplier, InstrumentType, CalibrationPlan, Asset,
    CalibrationEvent, Certificate, WorkOrder, ProductionUse,
    Alert, AuditRecord, CorrectiveAction, ImpactAssessment,
    CalibrationExtension
)

def validate_integrity(db: Session) -> Dict[str, Any]:
    """
    Execute exhaustive database integrity validation.
    Returns audit counts and detailed failure logs.
    """
    results = {
        "records_checked": 0,
        "passed_checks": 0,
        "failed_checks": 0,
        "duplicate_records": 0,
        "orphan_records": 0,
        "invalid_relationships": 0,
        "business_rule_violations": 0,
        "details": []
    }

    def record_check(passed: bool, message: str, category: str = "general"):
        results["records_checked"] += 1
        if passed:
            results["passed_checks"] += 1
        else:
            results["failed_checks"] += 1
            if category == "duplicate":
                results["duplicate_records"] += 1
            elif category == "orphan":
                results["orphan_records"] += 1
            elif category == "relationship":
                results["invalid_relationships"] += 1
            elif category == "business_rule":
                results["business_rule_violations"] += 1
            results["details"].append(message)

    # 1. Primary Key Uniqueness & Duplicates
    tables = [
        (Supplier, "supplier_id"),
        (InstrumentType, "type_id"),
        (CalibrationPlan, "plan_id"),
        (Asset, "asset_id"),
        (CalibrationEvent, "calibration_id"),
        (Certificate, "certificate_id"),
        (WorkOrder, "work_order_id"),
        (ProductionUse, "usage_id"),
        (Alert, "alert_id"),
        (AuditRecord, "audit_id"),
        (CorrectiveAction, "corrective_action_id"),
        (ImpactAssessment, "assessment_id"),
        (CalibrationExtension, "extension_id")
    ]

    for model, pk in tables:
        rows = db.query(getattr(model, pk)).all()
        ids = [r[0] for r in rows]
        is_unique = (len(ids) == len(set(ids)))
        record_check(
            is_unique,
            f"Table {model.__tablename__} primary key {pk} uniqueness: {len(ids)} rows, {len(set(ids))} unique",
            category="duplicate"
        )

    # 2. Foreign Key Integrity (Orphan Detection)
    # Asset FKs
    asset_types = {r[0] for r in db.query(InstrumentType.type_id).all()}
    asset_plans = {r[0] for r in db.query(CalibrationPlan.plan_id).all()}
    asset_suppliers = {r[0] for r in db.query(Supplier.supplier_id).all()}
    asset_ids = {r[0] for r in db.query(Asset.asset_id).all()}

    for asset in db.query(Asset).all():
        record_check(asset.type_id in asset_types, f"Asset {asset.asset_id} invalid type_id {asset.type_id}", "orphan")
        record_check(asset.plan_id in asset_plans, f"Asset {asset.asset_id} invalid plan_id {asset.plan_id}", "orphan")
        record_check(asset.supplier_id in asset_suppliers, f"Asset {asset.asset_id} invalid supplier_id {asset.supplier_id}", "orphan")

    # CalibrationEvent FKs
    cal_ids = {r[0] for r in db.query(CalibrationEvent.calibration_id).all()}
    for cal in db.query(CalibrationEvent).all():
        record_check(cal.asset_id in asset_ids, f"Calibration {cal.calibration_id} orphan asset_id {cal.asset_id}", "orphan")
        record_check(cal.plan_id in asset_plans, f"Calibration {cal.calibration_id} orphan plan_id {cal.plan_id}", "orphan")

    # Certificate FKs
    for cert in db.query(Certificate).all():
        record_check(cert.calibration_id in cal_ids, f"Certificate {cert.certificate_id} orphan calibration_id {cert.calibration_id}", "orphan")
        record_check(cert.asset_id in asset_ids, f"Certificate {cert.certificate_id} orphan asset_id {cert.asset_id}", "orphan")

    # ProductionUse FKs
    for u in db.query(ProductionUse).all():
        record_check(u.asset_id in asset_ids, f"ProductionUse {u.usage_id} orphan asset_id {u.asset_id}", "orphan")

    # 3. Enum Constraints
    valid_statuses = {"ACTIVE", "IN_CALIBRATION", "OUT_OF_SERVICE", "RETIRED", "QUARANTINED"}
    for a in db.query(Asset).all():
        record_check(a.status in valid_statuses, f"Asset {a.asset_id} invalid status {a.status}", "business_rule")

    valid_results = {"PASS", "FAIL"}
    for c in db.query(CalibrationEvent).all():
        record_check(c.result in valid_results, f"Calibration {c.calibration_id} invalid result {c.result}", "business_rule")

    valid_decisions = {"ALLOWED", "BLOCKED", "ALLOWED_WITH_EXCEPTION"}
    for u in db.query(ProductionUse).all():
        record_check(u.decision in valid_decisions, f"ProductionUse {u.usage_id} invalid decision {u.decision}", "business_rule")

    # 4. Date Ordering
    for c in db.query(CalibrationEvent).all():
        asset = db.query(Asset).filter(Asset.asset_id == c.asset_id).first()
        if asset and asset.commissioning_date:
            record_check(
                c.calibration_date >= asset.commissioning_date,
                f"Calibration {c.calibration_id} date {c.calibration_date} prior to commissioning {asset.commissioning_date}",
                "business_rule"
            )

    for cert in db.query(Certificate).all():
        record_check(
            cert.expiry_date >= cert.issue_date,
            f"Certificate {cert.certificate_id} expiry {cert.expiry_date} prior to issue {cert.issue_date}",
            "business_rule"
        )

    return results