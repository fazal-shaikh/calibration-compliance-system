"""
Controlled Anomaly Injection Engine
Deliberately introduces 4 labelled compliance anomalies into baseline data.
Strictly registers ground-truth metadata in separate ground_truth.csv.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from generator.ground_truth import save_ground_truth

def inject_anomalies(
    assets: List[Dict[str, Any]],
    plans: List[Dict[str, Any]],
    calibrations: List[Dict[str, Any]],
    certificates: List[Dict[str, Any]],
    production_uses: List[Dict[str, Any]],
    impact_assessments: List[Dict[str, Any]],
    corrective_actions: List[Dict[str, Any]],
    extensions: List[Dict[str, Any]],
    sim_date: datetime,
    rng: random.Random
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Inject exactly the 4 required edge cases while preserving baseline stability:
    1. Calibration due date inconsistent with calibration plan
    2. Expired instrument used without an approved exception
    3. Certificate referring to another asset
    4. Failed calibration not followed by an impact assessment
    """
    ground_truth_records = []
    anomaly_idx = 1
    plan_map = {p["plan_id"]: p for p in plans}
    ext_asset_ids = {ext["asset_id"] for ext in extensions if ext.get("status") == "ACTIVE"}

    # -------------------------------------------------------------------------
    # Scenario 1: Calibration due date inconsistent with calibration plan
    # -------------------------------------------------------------------------
    # Select 3 assets with valid last_calibration_date
    calibrated_assets = [a for a in assets if a.get("last_calibration_date") is not None]
    target_assets_s1 = calibrated_assets[:3] if len(calibrated_assets) >= 3 else calibrated_assets

    for asset in target_assets_s1:
        plan = plan_map[asset["plan_id"]]
        original_due = asset["next_due_date"]
        # Intentionally alter due date to be inconsistent with plan interval
        tampered_due = asset["last_calibration_date"] + timedelta(days=plan["interval_days"] + 73)
        asset["next_due_date"] = tampered_due

        ground_truth_records.append({
            "anomaly_id": f"ANOM-{anomaly_idx:04d}",
            "issue_type": "INCONSISTENT_DUE_DATE",
            "ground_truth": 1,
            "affected_entity_id": asset["asset_id"],
            "entity_type": "Asset",
            "expected_decision": "FLAG_INCONSISTENCY",
            "expected_detection_result": "ANOMALY_DETECTED",
            "description": (
                f"Asset {asset['asset_id']} due date {tampered_due.strftime('%Y-%m-%d')} is inconsistent "
                f"with plan interval of {plan['interval_days']} days (expected {original_due.strftime('%Y-%m-%d')})."
            ),
            "injected_at": sim_date.isoformat()
        })
        anomaly_idx += 1

    # -------------------------------------------------------------------------
    # Scenario 2: Expired instrument used without an approved exception
    # -------------------------------------------------------------------------
    # Must select overdue assets with NO active extension
    overdue_assets = [
        a for a in assets if a.get("next_due_date") and a["next_due_date"] < sim_date and a["asset_id"] not in ext_asset_ids
    ]
    if not overdue_assets:
        candidates = [a for a in assets if a["asset_id"] not in ext_asset_ids]
        overdue_assets = candidates[:3]
        for c_asset in overdue_assets:
            c_asset["next_due_date"] = sim_date - timedelta(days=20)

    for i, target_asset in enumerate(overdue_assets[:3]):
        use_time = sim_date - timedelta(days=2)
        u_id = f"USE-{target_asset['asset_id']}-{use_time.strftime('%Y%m%d%H%M%S')}-ANOM{i:02d}"
        
        tampered_use = {
            "usage_id": u_id,
            "asset_id": target_asset["asset_id"],
            "usage_timestamp": use_time,
            "batch_id": f"BATCH-ANOM-{i:03d}",
            "production_line": "Line-01",
            "operator_id": "OP-9999",
            "decision": "ALLOWED",  # Anomaly: Expired instrument allowed without exception!
            "policy_applied": "POL-BYPASS-UNAUTHORIZED",
            "reason": "Unauthorized shopfloor override bypassing calibration gate.",
            "validation_passed": False,
            "created_at": use_time
        }
        production_uses.append(tampered_use)

        ground_truth_records.append({
            "anomaly_id": f"ANOM-{anomaly_idx:04d}",
            "issue_type": "EXPIRED_INSTRUMENT_USAGE",
            "ground_truth": 1,
            "affected_entity_id": u_id,
            "entity_type": "ProductionUse",
            "expected_decision": "BLOCKED",
            "expected_detection_result": "ANOMALY_DETECTED",
            "description": (
                f"Production use {u_id} allowed expired instrument {target_asset['asset_id']} "
                f"(due {target_asset['next_due_date'].strftime('%Y-%m-%d')}) without approved emergency extension."
            ),
            "injected_at": sim_date.isoformat()
        })
        anomaly_idx += 1

    # -------------------------------------------------------------------------
    # Scenario 3: Certificate referring to another asset
    # -------------------------------------------------------------------------
    # Tamper 3 certificates so their asset_id points to another asset
    if len(certificates) >= 4 and len(assets) >= 2:
        for i in range(min(3, len(certificates))):
            cert = certificates[i]
            original_asset = cert["asset_id"]
            # Swap with a different asset
            other_asset = assets[(i + 1) % len(assets)]["asset_id"]
            if other_asset == original_asset:
                other_asset = assets[(i + 2) % len(assets)]["asset_id"]
            
            cert["asset_id"] = other_asset
            cert["verification_status"] = "MISMATCHED"

            ground_truth_records.append({
                "anomaly_id": f"ANOM-{anomaly_idx:04d}",
                "issue_type": "CERTIFICATE_ASSET_MISMATCH",
                "ground_truth": 1,
                "affected_entity_id": cert["certificate_id"],
                "entity_type": "Certificate",
                "expected_decision": "FLAG_MISMATCH",
                "expected_detection_result": "ANOMALY_DETECTED",
                "description": (
                    f"Certificate {cert['certificate_id']} references asset {other_asset}, "
                    f"but its calibration event {cert['calibration_id']} was performed on asset {original_asset}."
                ),
                "injected_at": sim_date.isoformat()
            })
            anomaly_idx += 1

    # -------------------------------------------------------------------------
    # Scenario 4: Failed calibration not followed by an impact assessment
    # -------------------------------------------------------------------------
    # Find or inject 3 failed calibration events that lack impact assessment & CAPA
    failed_cals = [c for c in calibrations if c.get("result") == "FAIL"]
    if len(failed_cals) >= 3:
        target_failed = failed_cals[:3]
        for fcal in target_failed:
            fcal_id = fcal["calibration_id"]
            # Suppress any existing impact assessment & CAPA for this calibration
            impact_assessments[:] = [ia for ia in impact_assessments if ia["calibration_id"] != fcal_id]
            corrective_actions[:] = [ca for ca in corrective_actions if ca["calibration_id"] != fcal_id]

            ground_truth_records.append({
                "anomaly_id": f"ANOM-{anomaly_idx:04d}",
                "issue_type": "MISSING_IMPACT_ASSESSMENT",
                "ground_truth": 1,
                "affected_entity_id": fcal_id,
                "entity_type": "CalibrationEvent",
                "expected_decision": "FLAG_MISSING_ASSESSMENT",
                "expected_detection_result": "ANOMALY_DETECTED",
                "description": (
                    f"Failed calibration event {fcal_id} on asset {fcal['asset_id']} has no associated "
                    "Impact Assessment or CAPA record recorded in database."
                ),
                "injected_at": sim_date.isoformat()
            })
            anomaly_idx += 1

    # Save isolated ground truth CSV
    save_ground_truth(ground_truth_records)

    return ground_truth_records, {
        "assets": assets,
        "plans": plans,
        "calibrations": calibrations,
        "certificates": certificates,
        "production_uses": production_uses,
        "impact_assessments": impact_assessments,
        "corrective_actions": corrective_actions
    }