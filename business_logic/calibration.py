"""
Calibration Math and Verification Business Logic
Formulaic computation of deviation, tolerance checking, and result determination.
"""

from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Any, Optional

def calculate_deviation(measured_value: float, reference_value: float) -> float:
    """
    Calculate absolute deviation between measured and reference standard.
    deviation = |measured_value - reference_value|
    """
    return round(abs(float(measured_value) - float(reference_value)), 6)

def evaluate_result(deviation: float, tolerance: float) -> str:
    """
    Evaluate PASS/FAIL result based on documented tolerance rules.
    PASS if deviation <= tolerance, else FAIL.
    """
    return "PASS" if round(deviation, 6) <= round(float(tolerance), 6) else "FAIL"

def calculate_next_due_date(calibration_date: datetime, interval_days: int) -> datetime:
    """
    Calculate the next scheduled calibration due date.
    next_due_date = calibration_date + timedelta(days=interval_days)
    """
    if isinstance(calibration_date, str):
        calibration_date = datetime.fromisoformat(calibration_date)
    return calibration_date + timedelta(days=int(interval_days))

def validate_calibration_record(
    measured_value: float,
    reference_value: float,
    tolerance: float,
    recorded_deviation: Optional[float] = None,
    recorded_result: Optional[str] = None
) -> Tuple[bool, float, str, List[str]]:
    """
    Validate calibration arithmetic integrity.
    Reconciles recorded deviation and result against calculated values.
    """
    errors = []
    expected_dev = calculate_deviation(measured_value, reference_value)
    expected_res = evaluate_result(expected_dev, tolerance)

    if recorded_deviation is not None:
        if abs(recorded_deviation - expected_dev) > 1e-4:
            errors.append(
                f"Deviation mismatch: recorded {recorded_deviation}, calculated {expected_dev}"
            )

    if recorded_result is not None:
        if recorded_result.upper() != expected_res:
            errors.append(
                f"Result mismatch: recorded {recorded_result}, expected {expected_res}"
            )

    is_valid = len(errors) == 0
    return is_valid, expected_dev, expected_res, errors