"""
Calibration Management Service
Handles empirical test registration, PASS/FAIL determination, certificate generation,
and failure workflows (CAPA, impact assessment, quarantine).
"""

import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models import (
    Asset, CalibrationEvent, Certificate, CalibrationPlan,
    ImpactAssessment, CorrectiveAction, WorkOrder, Alert
)
from business_logic.calibration import calculate_deviation, evaluate_result, calculate_next_due_date
from business_logic.corrective_actions import create_failure_containment
from services.audit_service import log_audit_event

class CalibrationService:
    def __init__(self, db: Session):
        self.db = db

    def record_calibration(
        self,
        asset_id: str,
        measured_value: float,
        reference_value: float,
        technician: str,
        calibration_date: Optional[datetime] = None,
        temperature: Optional[float] = 21.5,
        humidity: Optional[float] = 48.0,
        notes: Optional[str] = None,
        actor: str = "Metrologist"
    ) -> Dict[str, Any]:
        """
        Record a calibration test, compute deviation/result via formula,
        and trigger dependent actions (Certificate on PASS, CAPA/Impact on FAIL).
        """
        cal_date = calibration_date or datetime.utcnow()
        asset = self.db.query(Asset).filter(Asset.asset_id == asset_id).first()
        if not asset:
            raise ValueError(f"Asset {asset_id} not found.")

        plan = self.db.query(CalibrationPlan).filter(CalibrationPlan.plan_id == asset.plan_id).first()
        if not plan:
            raise ValueError(f"Plan {asset.plan_id} not found for asset {asset_id}.")

        tol = plan.tolerance
        dev = calculate_deviation(measured_value, reference_value)
        res = evaluate_result(dev, tol)

        cal_count = self.db.query(CalibrationEvent).count()
        cal_id = f"CAL-{asset_id}-2026-{(cal_count + 1):06d}"

        cal_event = CalibrationEvent(
            calibration_id=cal_id,
            asset_id=asset_id,
            plan_id=plan.plan_id,
            calibration_date=cal_date,
            technician=technician,
            measured_value=measured_value,
            reference_value=reference_value,
            tolerance=tol,
            deviation=dev,
            result=res,
            temperature_celsius=temperature,
            humidity_percent=humidity,
            notes=notes or ("Routine scheduled test" if res == "PASS" else "Out of tolerance exceedance"),
            created_at=cal_date
        )
        self.db.add(cal_event)

        certificate = None
        impact_assessment = None
        corrective_action = None

        if res == "PASS":
            # Update asset dates & status
            asset.last_calibration_date = cal_date
            next_due = calculate_next_due_date(cal_date, plan.interval_days)
            asset.next_due_date = next_due
            if asset.status in ["IN_CALIBRATION", "QUARANTINED"]:
                asset.status = "ACTIVE"
            asset.updated_at = cal_date

            # Issue Certificate
            cert_count = self.db.query(Certificate).count()
            cert_id = f"CERT-{cal_id}"
            cert_num = f"CERT-2026-{(cert_count + 1):06d}"
            sig_hash = hashlib.sha256(f"{cert_id}:{asset_id}:{cal_date}".encode()).hexdigest()

            certificate = Certificate(
                certificate_id=cert_id,
                certificate_number=cert_num,
                calibration_id=cal_id,
                asset_id=asset_id,
                issue_date=cal_date,
                expiry_date=next_due,
                verification_status="VALID",
                issuer_name="Quality Metrology Department",
                digital_signature_hash=sig_hash,
                file_path=f"/certs/2026/{cert_num}.pdf",
                created_at=cal_date
            )
            self.db.add(certificate)
        else:
            # Failure workflow
            asset.status = "QUARANTINED"
            asset.updated_at = cal_date

            # Load production uses for retrospective tracing
            from database.models import ProductionUse
            prod_uses = [
                u.to_dict() for u in self.db.query(ProductionUse).filter(ProductionUse.asset_id == asset_id).all()
            ]

            containment = create_failure_containment(
                calibration_id=cal_id,
                asset_id=asset_id,
                failure_date=cal_date,
                last_valid_calibration_date=asset.last_calibration_date,
                production_uses=prod_uses,
                technician=technician
            )

            ia_data = containment["impact_assessment"]
            ca_data = containment["corrective_action"]

            impact_assessment = ImpactAssessment(**ia_data)
            corrective_action = CorrectiveAction(**ca_data)
            self.db.add(impact_assessment)
            self.db.add(corrective_action)

            # Generate Critical Work Order
            wo_count = self.db.query(WorkOrder).count()
            wo = WorkOrder(
                work_order_id=f"WO-2026-{(wo_count + 1):06d}",
                asset_id=asset_id,
                order_type="FAILED_CALIBRATION",
                priority="CRITICAL",
                status="OPEN",
                assigned_technician=technician,
                creation_date=cal_date,
                scheduled_date=cal_date,
                downtime_hours=0.0,
                cost=0.0,
                resolution_notes="Immediate investigation required following calibration failure.",
                created_at=cal_date,
                updated_at=cal_date
            )
            self.db.add(wo)

            # Trigger Critical Alert
            alt_count = self.db.query(Alert).count()
            alt = Alert(
                alert_id=f"ALT-{(alt_count + 1):06d}",
                asset_id=asset_id,
                alert_type="FAILED_CALIBRATION",
                severity="CRITICAL",
                message=f"Critical failure on instrument {asset_id}. Asset quarantined.",
                status="ACTIVE",
                created_at=cal_date
            )
            self.db.add(alt)

        self.db.commit()

        log_audit_event(
            db=self.db,
            table_name="calibration_events",
            record_id=cal_id,
            action="INSERT",
            actor=actor,
            new_values=cal_event.to_dict(),
            reason=f"Calibration event recorded with result {res}."
        )

        return {
            "calibration_event": cal_event,
            "certificate": certificate,
            "impact_assessment": impact_assessment,
            "corrective_action": corrective_action,
            "result": res
        }

    def list_calibrations(self, asset_id: Optional[str] = None, result: Optional[str] = None) -> List[CalibrationEvent]:
        """Fetch calibration history."""
        query = self.db.query(CalibrationEvent).order_by(CalibrationEvent.calibration_date.desc())
        if asset_id:
            query = query.filter(CalibrationEvent.asset_id == asset_id)
        if result:
            query = query.filter(CalibrationEvent.result == result)
        return query.all()

    def list_certificates(self, asset_id: Optional[str] = None, status: Optional[str] = None) -> List[Certificate]:
        """Fetch certificates."""
        query = self.db.query(Certificate).order_by(Certificate.issue_date.desc())
        if asset_id:
            query = query.filter(Certificate.asset_id == asset_id)
        if status:
            query = query.filter(Certificate.verification_status == status)
        return query.all()