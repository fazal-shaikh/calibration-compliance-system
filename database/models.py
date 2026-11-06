"""
SQLAlchemy Data Models
Defines all 10 core entities and 4 supporting entities with complete constraints and relationships.
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Index
)
from sqlalchemy.orm import relationship
from database.connection import Base

class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id = Column(String(32), primary_key=True)
    name = Column(String(255), nullable=False)
    contact_email = Column(String(255))
    phone = Column(String(64))
    address = Column(String(500))
    is_accredited = Column(Boolean, nullable=False, default=True)
    accreditation_number = Column(String(128))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    assets = relationship("Asset", back_populates="supplier")

    def to_dict(self):
        return {
            "supplier_id": self.supplier_id,
            "name": self.name,
            "contact_email": self.contact_email,
            "phone": self.phone,
            "address": self.address,
            "is_accredited": self.is_accredited,
            "accreditation_number": self.accreditation_number,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class InstrumentType(Base):
    __tablename__ = "instrument_types"

    type_id = Column(String(32), primary_key=True)
    category = Column(String(64), nullable=False)  # Pressure, Temperature, Flow, Electrical, Dimensional, Weighing
    model_name = Column(String(255), nullable=False)
    manufacturer = Column(String(255), nullable=False)
    measurement_range = Column(String(128), nullable=False)
    default_interval_days = Column(Integer, nullable=False, default=365)
    default_tolerance = Column(Float, nullable=False, default=0.05)
    unit_of_measure = Column(String(32), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    assets = relationship("Asset", back_populates="instrument_type")
    calibration_plans = relationship("CalibrationPlan", back_populates="instrument_type")

    def to_dict(self):
        return {
            "type_id": self.type_id,
            "category": self.category,
            "model_name": self.model_name,
            "manufacturer": self.manufacturer,
            "measurement_range": self.measurement_range,
            "default_interval_days": self.default_interval_days,
            "default_tolerance": self.default_tolerance,
            "unit_of_measure": self.unit_of_measure,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class CalibrationPlan(Base):
    __tablename__ = "calibration_plans"

    plan_id = Column(String(32), primary_key=True)
    type_id = Column(String(32), ForeignKey("instrument_types.type_id"), nullable=False)
    name = Column(String(255), nullable=False)
    interval_days = Column(Integer, nullable=False)
    tolerance = Column(Float, nullable=False)
    mandatory_certificate = Column(Boolean, nullable=False, default=True)
    standard_operating_procedure = Column(String(500))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    instrument_type = relationship("InstrumentType", back_populates="calibration_plans")
    assets = relationship("Asset", back_populates="calibration_plan")
    calibration_events = relationship("CalibrationEvent", back_populates="calibration_plan")

    def to_dict(self):
        return {
            "plan_id": self.plan_id,
            "type_id": self.type_id,
            "name": self.name,
            "interval_days": self.interval_days,
            "tolerance": self.tolerance,
            "mandatory_certificate": self.mandatory_certificate,
            "standard_operating_procedure": self.standard_operating_procedure,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Asset(Base):
    __tablename__ = "assets"

    asset_id = Column(String(32), primary_key=True)
    serial_number = Column(String(128), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    type_id = Column(String(32), ForeignKey("instrument_types.type_id"), nullable=False)
    plan_id = Column(String(32), ForeignKey("calibration_plans.plan_id"), nullable=False)
    supplier_id = Column(String(32), ForeignKey("suppliers.supplier_id"), nullable=False)
    department = Column(String(128), nullable=False)
    location = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False)  # ACTIVE, IN_CALIBRATION, OUT_OF_SERVICE, RETIRED, QUARANTINED
    commissioning_date = Column(DateTime, nullable=False)
    last_calibration_date = Column(DateTime, nullable=True)
    next_due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    instrument_type = relationship("InstrumentType", back_populates="assets")
    calibration_plan = relationship("CalibrationPlan", back_populates="assets")
    supplier = relationship("Supplier", back_populates="assets")
    calibration_events = relationship("CalibrationEvent", back_populates="asset")
    certificates = relationship("Certificate", back_populates="asset")
    work_orders = relationship("WorkOrder", back_populates="asset")
    production_uses = relationship("ProductionUse", back_populates="asset")
    alerts = relationship("Alert", back_populates="asset")
    extensions = relationship("CalibrationExtension", back_populates="asset")

    def to_dict(self):
        return {
            "asset_id": self.asset_id,
            "serial_number": self.serial_number,
            "name": self.name,
            "type_id": self.type_id,
            "plan_id": self.plan_id,
            "supplier_id": self.supplier_id,
            "department": self.department,
            "location": self.location,
            "status": self.status,
            "commissioning_date": self.commissioning_date.isoformat() if self.commissioning_date else None,
            "last_calibration_date": self.last_calibration_date.isoformat() if self.last_calibration_date else None,
            "next_due_date": self.next_due_date.isoformat() if self.next_due_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class CalibrationEvent(Base):
    __tablename__ = "calibration_events"

    calibration_id = Column(String(64), primary_key=True)
    asset_id = Column(String(32), ForeignKey("assets.asset_id"), nullable=False)
    plan_id = Column(String(32), ForeignKey("calibration_plans.plan_id"), nullable=False)
    calibration_date = Column(DateTime, nullable=False)
    technician = Column(String(128), nullable=False)
    measured_value = Column(Float, nullable=False)
    reference_value = Column(Float, nullable=False)
    tolerance = Column(Float, nullable=False)
    deviation = Column(Float, nullable=False)
    result = Column(String(16), nullable=False)  # PASS, FAIL
    temperature_celsius = Column(Float)
    humidity_percent = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    asset = relationship("Asset", back_populates="calibration_events")
    calibration_plan = relationship("CalibrationPlan", back_populates="calibration_events")
    certificates = relationship("Certificate", back_populates="calibration_event")
    impact_assessments = relationship("ImpactAssessment", back_populates="calibration_event")
    corrective_actions = relationship("CorrectiveAction", back_populates="calibration_event")

    def to_dict(self):
        return {
            "calibration_id": self.calibration_id,
            "asset_id": self.asset_id,
            "plan_id": self.plan_id,
            "calibration_date": self.calibration_date.isoformat() if self.calibration_date else None,
            "technician": self.technician,
            "measured_value": self.measured_value,
            "reference_value": self.reference_value,
            "tolerance": self.tolerance,
            "deviation": self.deviation,
            "result": self.result,
            "temperature_celsius": self.temperature_celsius,
            "humidity_percent": self.humidity_percent,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Certificate(Base):
    __tablename__ = "certificates"

    certificate_id = Column(String(64), primary_key=True)
    certificate_number = Column(String(128), nullable=False, unique=True)
    calibration_id = Column(String(64), ForeignKey("calibration_events.calibration_id"), nullable=False)
    asset_id = Column(String(32), ForeignKey("assets.asset_id"), nullable=False)
    issue_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    verification_status = Column(String(32), nullable=False)  # VALID, EXPIRED, REVOKED, MISMATCHED
    issuer_name = Column(String(255), nullable=False)
    digital_signature_hash = Column(String(128))
    file_path = Column(String(500))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    calibration_event = relationship("CalibrationEvent", back_populates="certificates")
    asset = relationship("Asset", back_populates="certificates")

    def to_dict(self):
        return {
            "certificate_id": self.certificate_id,
            "certificate_number": self.certificate_number,
            "calibration_id": self.calibration_id,
            "asset_id": self.asset_id,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "verification_status": self.verification_status,
            "issuer_name": self.issuer_name,
            "digital_signature_hash": self.digital_signature_hash,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class WorkOrder(Base):
    __tablename__ = "work_orders"

    work_order_id = Column(String(64), primary_key=True)
    asset_id = Column(String(32), ForeignKey("assets.asset_id"), nullable=False)
    order_type = Column(String(64), nullable=False)  # UPCOMING_CALIBRATION, OVERDUE_CALIBRATION, FAILED_CALIBRATION, CORRECTIVE_MAINTENANCE, INVESTIGATION
    priority = Column(String(16), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(32), nullable=False)  # OPEN, IN_PROGRESS, PENDING_REVIEW, COMPLETED, CANCELLED
    assigned_technician = Column(String(128))
    creation_date = Column(DateTime, nullable=False)
    scheduled_date = Column(DateTime)
    completion_date = Column(DateTime, nullable=True)
    downtime_hours = Column(Float, nullable=False, default=0.0)
    cost = Column(Float, nullable=False, default=0.0)
    resolution_notes = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    asset = relationship("Asset", back_populates="work_orders")
    corrective_actions = relationship("CorrectiveAction", back_populates="work_order")

    def to_dict(self):
        return {
            "work_order_id": self.work_order_id,
            "asset_id": self.asset_id,
            "order_type": self.order_type,
            "priority": self.priority,
            "status": self.status,
            "assigned_technician": self.assigned_technician,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "downtime_hours": self.downtime_hours,
            "cost": self.cost,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ProductionUse(Base):
    __tablename__ = "production_uses"

    usage_id = Column(String(128), primary_key=True)
    asset_id = Column(String(32), ForeignKey("assets.asset_id"), nullable=False)
    usage_timestamp = Column(DateTime, nullable=False)
    batch_id = Column(String(128), nullable=False)
    production_line = Column(String(64), nullable=False)
    operator_id = Column(String(64), nullable=False)
    decision = Column(String(32), nullable=False)  # ALLOWED, BLOCKED, ALLOWED_WITH_EXCEPTION
    policy_applied = Column(String(64), nullable=False)
    reason = Column(Text, nullable=False)
    validation_passed = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    asset = relationship("Asset", back_populates="production_uses")

    def to_dict(self):
        return {
            "usage_id": self.usage_id,
            "asset_id": self.asset_id,
            "usage_timestamp": self.usage_timestamp.isoformat() if self.usage_timestamp else None,
            "batch_id": self.batch_id,
            "production_line": self.production_line,
            "operator_id": self.operator_id,
            "decision": self.decision,
            "policy_applied": self.policy_applied,
            "reason": self.reason,
            "validation_passed": self.validation_passed,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String(64), primary_key=True)
    asset_id = Column(String(32), ForeignKey("assets.asset_id"), nullable=True)
    alert_type = Column(String(64), nullable=False)
    severity = Column(String(16), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    message = Column(Text, nullable=False)
    status = Column(String(32), nullable=False)  # ACTIVE, ACKNOWLEDGED, RESOLVED, DISMISSED
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    asset = relationship("Asset", back_populates="alerts")

    def to_dict(self):
        return {
            "alert_id": self.alert_id,
            "asset_id": self.asset_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


class AuditRecord(Base):
    __tablename__ = "audit_records"

    audit_id = Column(String(64), primary_key=True)
    table_name = Column(String(64), nullable=False)
    record_id = Column(String(128), nullable=False)
    action = Column(String(16), nullable=False)  # INSERT, UPDATE, DELETE
    actor = Column(String(128), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    old_values_json = Column(Text, nullable=True)
    new_values_json = Column(Text, nullable=True)
    reason = Column(String(500), nullable=True)

    def to_dict(self):
        return {
            "audit_id": self.audit_id,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "action": self.action,
            "actor": self.actor,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "old_values_json": self.old_values_json,
            "new_values_json": self.new_values_json,
            "reason": self.reason
        }


class CorrectiveAction(Base):
    __tablename__ = "corrective_actions"

    corrective_action_id = Column(String(64), primary_key=True)
    calibration_id = Column(String(64), ForeignKey("calibration_events.calibration_id"), nullable=False)
    asset_id = Column(String(32), ForeignKey("assets.asset_id"), nullable=False)
    work_order_id = Column(String(64), ForeignKey("work_orders.work_order_id"), nullable=True)
    status = Column(String(32), nullable=False)  # OPEN, IN_PROGRESS, VERIFIED, CLOSED
    root_cause = Column(Text)
    containment_action = Column(Text)
    preventive_action = Column(Text)
    assigned_to = Column(String(128))
    target_date = Column(DateTime)
    closed_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    calibration_event = relationship("CalibrationEvent", back_populates="corrective_actions")
    work_order = relationship("WorkOrder", back_populates="corrective_actions")

    def to_dict(self):
        return {
            "corrective_action_id": self.corrective_action_id,
            "calibration_id": self.calibration_id,
            "asset_id": self.asset_id,
            "work_order_id": self.work_order_id,
            "status": self.status,
            "root_cause": self.root_cause,
            "containment_action": self.containment_action,
            "preventive_action": self.preventive_action,
            "assigned_to": self.assigned_to,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "closed_date": self.closed_date.isoformat() if self.closed_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ImpactAssessment(Base):
    __tablename__ = "impact_assessments"

    assessment_id = Column(String(64), primary_key=True)
    calibration_id = Column(String(64), ForeignKey("calibration_events.calibration_id"), nullable=False)
    asset_id = Column(String(32), ForeignKey("assets.asset_id"), nullable=False)
    investigation_status = Column(String(32), nullable=False)  # OPEN, IN_INVESTIGATION, CONCLUDED, DISPOSITIONED
    risk_level = Column(String(16), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    affected_batches_count = Column(Integer, nullable=False, default=0)
    affected_usage_events_count = Column(Integer, nullable=False, default=0)
    investigation_summary = Column(Text)
    disposition = Column(String(255))
    assessor = Column(String(128))
    assessment_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    closed_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    calibration_event = relationship("CalibrationEvent", back_populates="impact_assessments")

    def to_dict(self):
        return {
            "assessment_id": self.assessment_id,
            "calibration_id": self.calibration_id,
            "asset_id": self.asset_id,
            "investigation_status": self.investigation_status,
            "risk_level": self.risk_level,
            "affected_batches_count": self.affected_batches_count,
            "affected_usage_events_count": self.affected_usage_events_count,
            "investigation_summary": self.investigation_summary,
            "disposition": self.disposition,
            "assessor": self.assessor,
            "assessment_date": self.assessment_date.isoformat() if self.assessment_date else None,
            "closed_date": self.closed_date.isoformat() if self.closed_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class CalibrationExtension(Base):
    __tablename__ = "calibration_extensions"

    extension_id = Column(String(64), primary_key=True)
    asset_id = Column(String(32), ForeignKey("assets.asset_id"), nullable=False)
    original_due_date = Column(DateTime, nullable=False)
    extended_due_date = Column(DateTime, nullable=False)
    approved_by = Column(String(128), nullable=False)
    approval_date = Column(DateTime, nullable=False)
    justification = Column(Text, nullable=False)
    status = Column(String(32), nullable=False)  # ACTIVE, EXPIRED, SUPERSEDED, REVOKED
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    asset = relationship("Asset", back_populates="extensions")

    def to_dict(self):
        return {
            "extension_id": self.extension_id,
            "asset_id": self.asset_id,
            "original_due_date": self.original_due_date.isoformat() if self.original_due_date else None,
            "extended_due_date": self.extended_due_date.isoformat() if self.extended_due_date else None,
            "approved_by": self.approved_by,
            "approval_date": self.approval_date.isoformat() if self.approval_date else None,
            "justification": self.justification,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class WorkOrderAsset(Base):
    __tablename__ = "work_order_assets"

    id = Column(String(64), primary_key=True)
    work_order_id = Column(String(64), ForeignKey("work_orders.work_order_id"), nullable=False)
    asset_id = Column(String(32), ForeignKey("assets.asset_id"), nullable=False)
    role = Column(String(64), nullable=False, default="PRIMARY")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "work_order_id": self.work_order_id,
            "asset_id": self.asset_id,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }