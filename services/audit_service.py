"""
Audit Service
Centralized immutable audit logging and query capabilities.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models import AuditRecord

def log_audit_event(
    db: Session,
    table_name: str,
    record_id: str,
    action: str,
    actor: str,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None
) -> AuditRecord:
    """Record an immutable audit record in the database."""
    count = db.query(AuditRecord).count()
    audit_id = f"AUD-{(count + 1):06d}"

    def serialize(val):
        if not val:
            return None
        return json.dumps(val, default=str)

    rec = AuditRecord(
        audit_id=audit_id,
        table_name=table_name,
        record_id=record_id,
        action=action,
        actor=actor,
        timestamp=datetime.utcnow(),
        old_values_json=serialize(old_values),
        new_values_json=serialize(new_values),
        reason=reason
    )
    db.add(rec)
    db.commit()
    return rec

class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def list_audit_records(
        self,
        table_name: Optional[str] = None,
        record_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditRecord]:
        """Query audit records with optional filters."""
        query = self.db.query(AuditRecord).order_by(AuditRecord.timestamp.desc())

        if table_name:
            query = query.filter(AuditRecord.table_name == table_name)
        if record_id:
            query = query.filter(AuditRecord.record_id == record_id)
        if action:
            query = query.filter(AuditRecord.action == action)

        return query.limit(limit).all()