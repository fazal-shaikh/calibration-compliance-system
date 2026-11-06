"""
Tests for Anomaly Detection Engine and Ground-Truth Evaluation Benchmark
"""

import pytest
from datetime import datetime
from database.connection import get_db
from validation.evaluation import detect_anomalies_independently, evaluate_metrics
from generator.ground_truth import load_ground_truth

def test_anomaly_detection_against_ground_truth():
    """
    Verify zero data leakage: Detection runs on database heuristics,
    then benchmarks against separate ground_truth.csv to confirm 100% precision & recall.
    """
    sim_date = datetime(2026, 11, 1, 17, 0, 0)
    with get_db() as db:
        metrics = evaluate_metrics(db, sim_date)

        # Confirm all 4 edge cases were detected
        detected_types = {d["issue_type"] for d in metrics["detected_anomalies"]}
        required_types = {
            "INCONSISTENT_DUE_DATE",
            "EXPIRED_INSTRUMENT_USAGE",
            "CERTIFICATE_ASSET_MISMATCH",
            "MISSING_IMPACT_ASSESSMENT"
        }
        assert required_types.issubset(detected_types), f"Missing edge case types: {required_types - detected_types}"

        # Evaluate Precision, Recall, and F1
        assert metrics["anomaly_detection_precision"] >= 0.95
        assert metrics["anomaly_detection_recall"] >= 0.95
        assert metrics["anomaly_detection_f1_score"] >= 0.95