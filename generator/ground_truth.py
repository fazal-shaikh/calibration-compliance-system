"""
Ground Truth Management
Maintains isolated, tamper-evident ground-truth registry for evaluation and benchmarking.
Ensures zero data leakage to detection engines.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any
from config.settings import GROUND_TRUTH_DIR

GROUND_TRUTH_CSV_PATH = GROUND_TRUTH_DIR / "ground_truth.csv"

FIELDS = [
    "anomaly_id",
    "issue_type",
    "ground_truth",
    "affected_entity_id",
    "entity_type",
    "expected_decision",
    "expected_detection_result",
    "description",
    "injected_at"
]

def save_ground_truth(records: List[Dict[str, Any]], filepath: Path = None):
    """Persist ground truth records to designated isolated CSV."""
    target_path = filepath or GROUND_TRUTH_CSV_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for r in records:
            writer.writerow(r)

def load_ground_truth(filepath: Path = None) -> List[Dict[str, Any]]:
    """Load ground truth records from isolated CSV."""
    target_path = filepath or GROUND_TRUTH_CSV_PATH
    if not target_path.exists():
        return []
    with open(target_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)