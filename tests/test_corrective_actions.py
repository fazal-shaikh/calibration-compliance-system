"""
Tests for Corrective Actions, Impact Assessment, and Retrospective Lot Tracing
"""

import pytest
from datetime import datetime, timedelta
from business_logic.corrective_actions import trace_affected_production, create_failure_containment

def test_retrospective_lot_tracing():
    """Verify correct isolation of production batches processed prior to failure."""
    failure_date = datetime(2026, 7, 1, 12, 0, 0)
    last_valid_cal = datetime(2026, 1, 1, 8, 0, 0)

    production_uses = [
        # In-window event 1
        {"usage_id": "U-1", "asset_id": "AST-001", "batch_id": "BATCH-100", "usage_timestamp": datetime(2026, 3, 1)},
        # In-window event 2 (same batch)
        {"usage_id": "U-2", "asset_id": "AST-001", "batch_id": "BATCH-100", "usage_timestamp": datetime(2026, 4, 1)},
        # In-window event 3 (different batch)
        {"usage_id": "U-3", "asset_id": "AST-001", "batch_id": "BATCH-200", "usage_timestamp": datetime(2026, 5, 1)},
        # Out-of-window (after failure)
        {"usage_id": "U-4", "asset_id": "AST-001", "batch_id": "BATCH-300", "usage_timestamp": datetime(2026, 7, 2)},
        # Different asset
        {"usage_id": "U-5", "asset_id": "AST-002", "batch_id": "BATCH-400", "usage_timestamp": datetime(2026, 3, 1)}
    ]

    trace = trace_affected_production("AST-001", failure_date, last_valid_cal, production_uses)
    assert trace["affected_usage_events_count"] == 3
    assert set(trace["affected_batches"]) == {"BATCH-100", "BATCH-200"}
    assert trace["affected_batches_count"] == 2

def test_failure_containment_workflow():
    """Verify complete failure containment package generation."""
    failure_date = datetime(2026, 7, 1)
    uses = [
        {"usage_id": "U-1", "asset_id": "AST-001", "batch_id": "BATCH-1", "usage_timestamp": datetime(2026, 6, 1)}
    ]
    containment = create_failure_containment(
        calibration_id="CAL-AST-001-2026-000001",
        asset_id="AST-001",
        failure_date=failure_date,
        last_valid_calibration_date=datetime(2026, 1, 1),
        production_uses=uses
    )

    ia = containment["impact_assessment"]
    ca = containment["corrective_action"]

    assert ia["calibration_id"] == "CAL-AST-001-2026-000001"
    assert ia["investigation_status"] == "OPEN"
    assert ia["affected_batches_count"] == 1

    assert ca["calibration_id"] == "CAL-AST-001-2026-000001"
    assert ca["status"] == "OPEN"
    assert "quarantine" in ca["containment_action"].lower()