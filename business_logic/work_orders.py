"""
Work Order Management Business Logic
Automates generation, priority assignment, status transitions, and downtime tracking.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

def create_work_order(
    work_order_id: str,
    asset_id: str,
    order_type: str,
    priority: str,
    creation_date: datetime,
    assigned_technician: Optional[str] = None,
    scheduled_date: Optional[datetime] = None,
    status: str = "OPEN"
) -> Dict[str, Any]:
    """Factory function for structured work order creation."""
    return {
        "work_order_id": work_order_id,
        "asset_id": asset_id,
        "order_type": order_type,
        "priority": priority,
        "status": status,
        "assigned_technician": assigned_technician,
        "creation_date": creation_date,
        "scheduled_date": scheduled_date or (creation_date + timedelta(days=3)),
        "completion_date": None,
        "downtime_hours": 0.0,
        "cost": 0.0,
        "resolution_notes": None,
        "created_at": creation_date,
        "updated_at": creation_date
    }

def complete_work_order(
    work_order: Dict[str, Any],
    completion_date: datetime,
    downtime_hours: float,
    cost: float,
    resolution_notes: str
) -> Dict[str, Any]:
    """Transition work order to COMPLETED state and record downtime/cost."""
    work_order["status"] = "COMPLETED"
    work_order["completion_date"] = completion_date
    work_order["downtime_hours"] = max(0.0, float(downtime_hours))
    work_order["cost"] = max(0.0, float(cost))
    work_order["resolution_notes"] = resolution_notes
    work_order["updated_at"] = completion_date
    return work_order

def calculate_mttr_hours(completed_work_orders: List[Dict[str, Any]]) -> float:
    """
    Calculate Mean Time to Repair (MTTR) in hours across completed maintenance/repair work orders.
    Formula: Total repair hours / Number of completed repair orders.
    """
    durations = []
    repair_types = {"FAILED_CALIBRATION", "CORRECTIVE_MAINTENANCE"}
    for wo in completed_work_orders:
        if wo.get("status") == "COMPLETED" and wo.get("order_type") in repair_types:
            c_date = wo.get("creation_date")
            comp_date = wo.get("completion_date")
            if isinstance(c_date, str):
                c_date = datetime.fromisoformat(c_date)
            if isinstance(comp_date, str):
                comp_date = datetime.fromisoformat(comp_date)
            if c_date and comp_date and comp_date >= c_date:
                hours = (comp_date - c_date).total_seconds() / 3600.0
                durations.append(hours)

    if not durations:
        return 0.0
    return round(sum(durations) / len(durations), 2)