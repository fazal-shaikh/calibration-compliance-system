"""
Instrument Management Service
Provides high-level business APIs for instrument registration, retrieval, status lifecycle, and extensions.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models import Asset, InstrumentType, CalibrationPlan, Supplier, CalibrationExtension
from services.audit_service import log_audit_event

class InstrumentService:
    def __init__(self, db: Session):
        self.db = db

    def get_instrument_by_id(self, asset_id: str) -> Optional[Asset]:
        """Fetch asset by ID."""
        return self.db.query(Asset).filter(Asset.asset_id == asset_id).first()

    def list_instruments(
        self,
        status: Optional[str] = None,
        department: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Asset]:
        """Query instruments with multi-criteria filtering."""
        query = self.db.query(Asset).join(InstrumentType)

        if status:
            query = query.filter(Asset.status == status)
        if department:
            query = query.filter(Asset.department == department)
        if category:
            query = query.filter(InstrumentType.category == category)
        if search:
            search_fmt = f"%{search}%"
            query = query.filter(
                (Asset.asset_id.ilike(search_fmt)) |
                (Asset.serial_number.ilike(search_fmt)) |
                (Asset.name.ilike(search_fmt))
            )

        return query.all()

    def register_instrument(
        self,
        serial_number: str,
        name: str,
        type_id: str,
        plan_id: str,
        supplier_id: str,
        department: str,
        location: str,
        commissioning_date: datetime,
        actor: str = "Admin"
    ) -> Asset:
        """Register a new physical instrument with deterministic ID."""
        count = self.db.query(Asset).count()
        asset_id = f"AST-{(count + 1):06d}"

        new_asset = Asset(
            asset_id=asset_id,
            serial_number=serial_number,
            name=name,
            type_id=type_id,
            plan_id=plan_id,
            supplier_id=supplier_id,
            department=department,
            location=location,
            status="ACTIVE",
            commissioning_date=commissioning_date,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(new_asset)
        self.db.commit()

        log_audit_event(
            db=self.db,
            table_name="assets",
            record_id=asset_id,
            action="INSERT",
            actor=actor,
            new_values=new_asset.to_dict(),
            reason="Manual registration of new instrument."
        )
        return new_asset

    def update_status(self, asset_id: str, new_status: str, actor: str, reason: str) -> Optional[Asset]:
        """Update operational status with audit log."""
        asset = self.get_instrument_by_id(asset_id)
        if not asset:
            return None

        old_values = asset.to_dict()
        asset.status = new_status
        asset.updated_at = datetime.utcnow()
        self.db.commit()

        log_audit_event(
            db=self.db,
            table_name="assets",
            record_id=asset_id,
            action="UPDATE",
            actor=actor,
            old_values=old_values,
            new_values=asset.to_dict(),
            reason=reason
        )
        return asset

    def grant_extension(
        self,
        asset_id: str,
        extended_due_date: datetime,
        approved_by: str,
        justification: str
    ) -> Optional[CalibrationExtension]:
        """Authorize and grant an emergency calibration extension."""
        asset = self.get_instrument_by_id(asset_id)
        if not asset:
            return None

        ext_count = self.db.query(CalibrationExtension).count()
        ext_id = f"EXT-2026-{(ext_count + 1):06d}"

        extension = CalibrationExtension(
            extension_id=ext_id,
            asset_id=asset_id,
            original_due_date=asset.next_due_date or datetime.utcnow(),
            extended_due_date=extended_due_date,
            approved_by=approved_by,
            approval_date=datetime.utcnow(),
            justification=justification,
            status="ACTIVE",
            created_at=datetime.utcnow()
        )
        self.db.add(extension)
        self.db.commit()

        log_audit_event(
            db=self.db,
            table_name="calibration_extensions",
            record_id=ext_id,
            action="INSERT",
            actor=approved_by,
            new_values=extension.to_dict(),
            reason="Emergency calibration extension approved."
        )
        return extension