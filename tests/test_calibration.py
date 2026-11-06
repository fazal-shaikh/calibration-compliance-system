"""
Tests for Calibration Math, Tolerance Rules, and Due-Date Computations
"""

import pytest
from datetime import datetime, timedelta
from business_logic.calibration import (
    calculate_deviation, evaluate_result,
    calculate_next_due_date, validate_calibration_record
)

def test_deviation_calculation():
    """Verify exact absolute deviation calculation."""
    assert calculate_deviation(100.05, 100.0) == 0.05
    assert calculate_deviation(99.95, 100.0) == 0.05
    assert calculate_deviation(50.0, 50.0) == 0.0

def test_tolerance_evaluation_boundary_conditions():
    """Verify strict PASS/FAIL logic at boundary thresholds."""
    tol = 0.05
    
    # Strictly inside
    assert evaluate_result(0.0499, tol) == "PASS"
    
    # Exact boundary condition: deviation == tolerance MUST PASS
    assert evaluate_result(0.0500, tol) == "PASS"
    
    # Strictly outside boundary condition: deviation > tolerance MUST FAIL
    assert evaluate_result(0.0501, tol) == "FAIL"
    assert evaluate_result(0.12, tol) == "FAIL"

def test_next_due_date_calculation():
    """Verify calendar addition of calibration intervals."""
    cal_date = datetime(2026, 3, 1, 10, 0, 0)
    due_180 = calculate_next_due_date(cal_date, 180)
    assert due_180 == cal_date + timedelta(days=180)

    due_365 = calculate_next_due_date(cal_date, 365)
    assert due_365 == cal_date + timedelta(days=365)

def test_arithmetic_reconciliation_validator():
    """Verify calibration record arithmetic validator identifies tampered results."""
    # Valid record
    is_valid, dev, res, errors = validate_calibration_record(
        measured_value=100.02,
        reference_value=100.00,
        tolerance=0.05,
        recorded_deviation=0.02,
        recorded_result="PASS"
    )
    assert is_valid is True
    assert len(errors) == 0

    # Tampered result
    is_valid, dev, res, errors = validate_calibration_record(
        measured_value=100.08,
        reference_value=100.00,
        tolerance=0.05,
        recorded_deviation=0.08,
        recorded_result="PASS"  # Tampered! 0.08 > 0.05 should be FAIL
    )
    assert is_valid is False
    assert any("Result mismatch" in err for err in errors)