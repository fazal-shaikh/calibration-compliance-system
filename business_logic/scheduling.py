"""
Calibration Scheduling Business Logic
Manages next due dates, upcoming calibration forecasts, overdue detections, and emergency extension reconciliations.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

def is_overdue(due_date: datetime, as_of_date: datetime) -> bool:
    """Check if an instrument has passed its due date without grace period."""
    if due_date is None:
        return True
    if isinstance(due_date, str):
        due_date = datetime.fromisoformat(due_date)
    if isinstance(as_of_date, str):
        as_of_date = datetime.fromisoformat(as_of_date)
    return as_of_date > due_date

def is_upcoming(due_date: datetime, as_of_date: datetime, window_days: int = 30) -> bool:
    """Check if an instrument is within the upcoming calibration notification window."""
    if due_date is None:
        return False
    if isinstance(due_date, str):
        due_date = datetime.fromisoformat(due_date)
    if isinstance(as_of_date, str):
        as_of_date = datetime.fromisoformat(as_of_date)
    return as_of_date <= due_date <= (as_of_date + timedelta(days=window_days))

def check_active_extension(
    asset_id: str,
    extensions: List[Dict[str, Any]],
    as_of_date: datetime
) -> Optional[Dict[str, Any]]:
    """
    Check if an asset has a valid, approved, active extension covering the target date.
    """
    if isinstance(as_of_date, str):
        as_of_date = datetime.fromisoformat(as_of_date)

    for ext in extensions:
        if ext.get("asset_id") == asset_id and ext.get("status") == "ACTIVE":
            ext_due = ext.get("extended_due_date")
            if isinstance(ext_due, str):
                ext_due = datetime.fromisoformat(ext_due)
            if ext_due >= as_of_date:
                return ext
    return None

def calculate_effective_due_date(
    base_due_date: datetime,
    active_extension: Optional[Dict[str, Any]] = None
) -> datetime:
    """
    Return effective due date considering emergency extensions while preserving original.
    """
    if active_extension:
        ext_date = active_extension.get("extended_due_date")
        if isinstance(ext_date, str):
            return datetime.fromisoformat(ext_date)
        return ext_date
    return base_due_date