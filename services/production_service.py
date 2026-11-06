"""
Production Usage Service
Executes real-time compliance gatekeeper checks and registers shopfloor use events.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models import (
    Asset, CalibrationEvent, Certificate, WorkOrder,
    CalibrationExtension, ProductionUse, Alert
)
from business_logic.production_validation import evaluate_production_usage
from services.audit_service import log_audit_event

class ProductionService:
    def __init__(self, db: Session):
        self.db = db

    def validate_and_record_usage(
        self,
        asset_id: str,
        batch_id: str,
        production_line: str,
        operator_id: str,
        usage_timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Evaluate shopfloor instrument usage request against 8 compliance gates.
        Persists decision and creates alert if unauthorized.
        """
        now = usage_timestamp or datetime.utcnow()
        asset = self.db.query(Asset).filter(Asset.asset_id == asset_id).first()

        latest_cal = (
            self.db.query(CalibrationEvent)
            .filter(CalibrationEvent.asset_id == asset_id, CalibrationEvent.calibration_date <= now)
            .order_by(CalibrationEvent.calibration_date.desc())
            .first()
        )

        cert = (
            self.db.query(Certificate)
            .filter(Certificate.asset_id == asset_id)
            .order_by(Certificate.issue_date.desc())
            .first()
        )

        active_wos = (
            self.db.query(WorkOrder)
            .filter(WorkOrder.asset_id == asset_id, WorkOrder.status.in_(["OPEN", "IN_PROGRESS"]))
            .all()
        )

        active_ext = (
            self.db.query(CalibrationExtension)
            .filter(CalibrationExtension.asset_id == asset_id, CalibrationExtension.status == "ACTIVE")
            .first()
        )

        eval_res = evaluate_production_usage(
            asset=asset.to_dict() if asset else None,
            usage_timestamp=now,
            latest_calibration=latest_cal.to_dict() if latest_cal else None,
            certificate=cert.to_dict() if cert else None,
            active_work_orders=[w.to_dict() for w in active_wos],
            active_extension=active_ext.to_dict() if active_ext else None
        )

        use_count = self.db.query(ProductionUse).count()
        time_str = now.strftime("%Y%m%d%H%M%S")
        usage_id = f"USE-{asset_id}-{time_str}-{(use_count + 1):06d}"

        use_rec = ProductionUse(
            usage_id=usage_id,
            asset_id=asset_id,
            usage_timestamp=now,
            batch_id=batch_id,
            production_line=production_line,
            operator_id=operator_id,
            decision=eval_res["decision"],
            policy_applied=eval_res["policy_applied"],
            reason=eval_res["reason"],
            validation_passed=eval_res["validation_passed"],
            created_at=now
        )
        self.db.add(use_rec)

        # Alert if blocked due to critical compliance hazard
        if eval_res["decision"] == "BLOCKED":
            alt_count = self.db.query(Alert).count()
            alt = Alert(
                alert_id=f"ALT-{(alt_count + 1):06d}",
                asset_id=asset_id,
                alert_type="UNAUTHORIZED_USAGE",
                severity="CRITICAL",
                message=f"Unauthorized usage BLOCKED for {asset_id} on {production_line} (Batch {batch_id}): {eval_res['reason']}",
                status="ACTIVE",
                created_at=now
            )
            self.db.add(alt)

        self.db.commit()

        return {
            "usage_record": use_rec,
            "decision": eval_res["decision"],
            "policy_applied": eval_res["policy_applied"],
            "reason": eval_res["reason"],
            "validation_passed": eval_res["validation_passed"]
        }

    def list_production_uses(
        self,
        asset_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        decision: Optional[str] = None,
        limit: int = 200
    ) -> List[ProductionUse]:
        """Fetch production uses with filters."""
        query = self.db.query(ProductionUse).order_by(ProductionUse.usage_timestamp.desc())
        if asset_id:
            query = query.filter(ProductionUse.asset_id == asset_id)
        if batch_id:
            query = query.filter(ProductionUse.batch_id == batch_id)
        if decision:
            query = query.filter(ProductionUse.decision == decision)
        return query.limit(limit).all()