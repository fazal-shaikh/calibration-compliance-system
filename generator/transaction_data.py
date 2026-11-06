"""
Transaction Data Generator
Generates realistic CalibrationEvents, Certificates, WorkOrders, ProductionUses,
Alerts, AuditRecords, CorrectiveActions, ImpactAssessments, and Extensions.
"""

import hashlib
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from config.settings import REFERENCE_YEAR
from business_logic.calibration import calculate_deviation, evaluate_result, calculate_next_due_date
from business_logic.production_validation import evaluate_production_usage

TECHNICIANS = [
    "Sarah Chen (Lead Metrologist)",
    "Mark Davis (Calibration Specialist)",
    "Alex Rivera (Senior Tech)",
    "Priya Sharma (Quality Engineer)",
    "Hans Gruber (Instrumentation Specialist)",
    "Elena Rostova (Metrology Inspector)"
]

OPERATORS = [f"OP-{i:04d}" for i in range(101, 150)]
BATCH_PREFIX = "BATCH-2026-"

def generate_calibration_and_certificates(
    calibration_count: int,
    assets: List[Dict[str, Any]],
    plans: List[Dict[str, Any]],
    suppliers: List[Dict[str, Any]],
    rng: random.Random
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generate deterministic CalibrationEvents, Certificates, CorrectiveActions, and ImpactAssessments.
    Calculates derived statuses, next due dates, and PASS/FAIL evaluations according to tolerance rules.
    """
    plan_map = {p["plan_id"]: p for p in plans}
    supplier_map = {s["supplier_id"]: s for s in suppliers}

    calibrations = []
    certificates = []
    corrective_actions = []
    impact_assessments = []

    # Reference year start and end (2026)
    start_date = datetime(REFERENCE_YEAR, 1, 1, 8, 0, 0)

    # Sort assets deterministically
    sorted_assets = sorted(assets, key=lambda x: x["asset_id"])
    active_assets = [a for a in sorted_assets if a["status"] != "RETIRED"]

    cal_seq = 1
    cert_seq = 1
    capa_seq = 1
    imp_seq = 1

    # First pass: ensure all active assets get at least one baseline calibration early in the year
    for asset in active_assets:
        plan = plan_map[asset["plan_id"]]
        # Stagger initial calibrations across first 120 days
        cal_date = start_date + timedelta(days=rng.randint(1, 120), hours=rng.randint(8, 16))
        
        # Reference value based on category tolerance
        ref_val = 100.0
        tol = plan["tolerance"]
        
        # 95% pass, 5% fail
        is_pass = rng.random() < 0.95
        if is_pass:
            # deviation within tolerance
            dev = round(rng.uniform(0.0001, tol * 0.95), 5)
        else:
            # deviation strictly exceeds tolerance
            dev = round(rng.uniform(tol * 1.05, tol * 2.5), 5)

        meas_val = round(ref_val + (dev if rng.random() < 0.5 else -dev), 5)
        calc_dev = calculate_deviation(meas_val, ref_val)
        calc_res = evaluate_result(calc_dev, tol)

        cal_id = f"CAL-{asset['asset_id']}-2026-{cal_seq:06d}"
        cal_seq += 1

        cal_rec = {
            "calibration_id": cal_id,
            "asset_id": asset["asset_id"],
            "plan_id": plan["plan_id"],
            "calibration_date": cal_date,
            "technician": rng.choice(TECHNICIANS),
            "measured_value": meas_val,
            "reference_value": ref_val,
            "tolerance": tol,
            "deviation": calc_dev,
            "result": calc_res,
            "temperature_celsius": round(rng.uniform(20.0, 23.5), 1),
            "humidity_percent": round(rng.uniform(42.0, 58.0), 1),
            "notes": "Routine scheduled calibration." if calc_res == "PASS" else "Calibration failed: out of tolerance.",
            "created_at": cal_date
        }
        calibrations.append(cal_rec)

        # Update asset calibration timestamps
        asset["last_calibration_date"] = cal_date
        next_due = calculate_next_due_date(cal_date, plan["interval_days"])
        asset["next_due_date"] = next_due

        cal_cert_due = calculate_next_due_date(cal_date, plan["interval_days"])

        if calc_res == "PASS":
            cert_id = f"CERT-{cal_id}"
            cert_num = f"CERT-2026-{cert_seq:06d}"
            cert_seq += 1
            supplier = supplier_map.get(asset["supplier_id"], suppliers[0])
            sig_hash = hashlib.sha256(f"{cert_id}:{asset['asset_id']}:{cal_date}".encode()).hexdigest()

            certificates.append({
                "certificate_id": cert_id,
                "certificate_number": cert_num,
                "calibration_id": cal_id,
                "asset_id": asset["asset_id"],
                "issue_date": cal_date,
                "expiry_date": cal_cert_due,
                "verification_status": "VALID",
                "issuer_name": supplier["name"],
                "digital_signature_hash": sig_hash,
                "file_path": f"/certs/2026/{cert_num}.pdf",
                "created_at": cal_date
            })
        else:
            # Handle failure containment
            asset["status"] = "QUARANTINED"
            capa_id = f"CAPA-2026-{capa_seq:06d}"
            imp_id = f"IMP-2026-{imp_seq:06d}"
            capa_seq += 1
            imp_seq += 1

            impact_assessments.append({
                "assessment_id": imp_id,
                "calibration_id": cal_id,
                "asset_id": asset["asset_id"],
                "investigation_status": "OPEN",
                "risk_level": "HIGH",
                "affected_batches_count": rng.randint(2, 12),
                "affected_usage_events_count": rng.randint(15, 60),
                "investigation_summary": f"Retrospective trace on out-of-tolerance failure for {asset['asset_id']}.",
                "disposition": "Quarantined Pending Batch Review",
                "assessor": rng.choice(TECHNICIANS),
                "assessment_date": cal_date,
                "closed_date": None,
                "created_at": cal_date
            })

            corrective_actions.append({
                "corrective_action_id": capa_id,
                "calibration_id": cal_id,
                "asset_id": asset["asset_id"],
                "work_order_id": None,
                "status": "OPEN",
                "root_cause": "Sensor drift due to thermal cycling.",
                "containment_action": "Quarantine instrument and tag affected WIP lots.",
                "preventive_action": "Review calibration frequency and tighten environmental controls.",
                "assigned_to": rng.choice(TECHNICIANS),
                "target_date": cal_date + timedelta(days=14),
                "closed_date": None,
                "created_at": cal_date
            })

    # Remaining calibrations up to target calibration_count
    while len(calibrations) < calibration_count:
        asset = rng.choice(active_assets)
        plan = plan_map[asset["plan_id"]]
        
        # Subsequent calibration dates later in the year
        days_after = rng.randint(120, 350)
        cal_date = start_date + timedelta(days=days_after, hours=rng.randint(8, 16))
        
        ref_val = 100.0
        tol = plan["tolerance"]
        is_pass = rng.random() < 0.96
        if is_pass:
            dev = round(rng.uniform(0.0001, tol * 0.95), 5)
        else:
            dev = round(rng.uniform(tol * 1.05, tol * 2.2), 5)

        meas_val = round(ref_val + (dev if rng.random() < 0.5 else -dev), 5)
        calc_dev = calculate_deviation(meas_val, ref_val)
        calc_res = evaluate_result(calc_dev, tol)

        cal_id = f"CAL-{asset['asset_id']}-2026-{cal_seq:06d}"
        cal_seq += 1

        calibrations.append({
            "calibration_id": cal_id,
            "asset_id": asset["asset_id"],
            "plan_id": plan["plan_id"],
            "calibration_date": cal_date,
            "technician": rng.choice(TECHNICIANS),
            "measured_value": meas_val,
            "reference_value": ref_val,
            "tolerance": tol,
            "deviation": calc_dev,
            "result": calc_res,
            "temperature_celsius": round(rng.uniform(20.0, 23.5), 1),
            "humidity_percent": round(rng.uniform(42.0, 58.0), 1),
            "notes": "Follow-up verification test." if calc_res == "PASS" else "Tolerance exceedance during periodic audit.",
            "created_at": cal_date
        })

        # Update asset if this is more recent
        if asset["last_calibration_date"] is None or cal_date > asset["last_calibration_date"]:
            asset["last_calibration_date"] = cal_date
            next_due = calculate_next_due_date(cal_date, plan["interval_days"])
            asset["next_due_date"] = next_due

        cal_cert_due = calculate_next_due_date(cal_date, plan["interval_days"])

        if calc_res == "PASS":
            cert_id = f"CERT-{cal_id}"
            cert_num = f"CERT-2026-{cert_seq:06d}"
            cert_seq += 1
            supplier = supplier_map.get(asset["supplier_id"], suppliers[0])
            sig_hash = hashlib.sha256(f"{cert_id}:{asset['asset_id']}:{cal_date}".encode()).hexdigest()

            certificates.append({
                "certificate_id": cert_id,
                "certificate_number": cert_num,
                "calibration_id": cal_id,
                "asset_id": asset["asset_id"],
                "issue_date": cal_date,
                "expiry_date": cal_cert_due,
                "verification_status": "VALID",
                "issuer_name": supplier["name"],
                "digital_signature_hash": sig_hash,
                "file_path": f"/certs/2026/{cert_num}.pdf",
                "created_at": cal_date
            })
        else:
            asset["status"] = "QUARANTINED"
            capa_id = f"CAPA-2026-{capa_seq:06d}"
            imp_id = f"IMP-2026-{imp_seq:06d}"
            capa_seq += 1
            imp_seq += 1

            impact_assessments.append({
                "assessment_id": imp_id,
                "calibration_id": cal_id,
                "asset_id": asset["asset_id"],
                "investigation_status": "OPEN",
                "risk_level": "HIGH",
                "affected_batches_count": rng.randint(1, 8),
                "affected_usage_events_count": rng.randint(10, 45),
                "investigation_summary": f"Retrospective impact trace following calibration failure on {asset['asset_id']}.",
                "disposition": "Quarantined Pending Batch Review",
                "assessor": rng.choice(TECHNICIANS),
                "assessment_date": cal_date,
                "closed_date": None,
                "created_at": cal_date
            })

            corrective_actions.append({
                "corrective_action_id": capa_id,
                "calibration_id": cal_id,
                "asset_id": asset["asset_id"],
                "work_order_id": None,
                "status": "OPEN",
                "root_cause": "Wear and tear on sensor membrane.",
                "containment_action": "Quarantine instrument and check recent production lots.",
                "preventive_action": "Re-zero sensor and conduct recalibration.",
                "assigned_to": rng.choice(TECHNICIANS),
                "target_date": cal_date + timedelta(days=14),
                "closed_date": None,
                "created_at": cal_date
            })

    return calibrations, certificates, corrective_actions, impact_assessments

def generate_work_orders(
    assets: List[Dict[str, Any]],
    calibrations: List[Dict[str, Any]],
    sim_date: datetime,
    rng: random.Random
) -> List[Dict[str, Any]]:
    """
    Generate work orders for upcoming calibrations, overdue instruments, and failures.
    Includes realistic downtime, costs, and statuses (COMPLETED vs OPEN).
    """
    work_orders = []
    wo_seq = 1

    # 1. Orders for failed calibrations
    for cal in calibrations:
        if cal["result"] == "FAIL":
            wo_id = f"WO-2026-{wo_seq:06d}"
            wo_seq += 1
            c_date = cal["calibration_date"]
            # 50% completed, 50% open/in-progress
            is_completed = rng.random() < 0.5
            comp_date = c_date + timedelta(hours=rng.randint(6, 48)) if is_completed else None
            dt_hours = round(rng.uniform(4.0, 36.0), 1) if is_completed else round(rng.uniform(2.0, 12.0), 1)
            cost = round(rng.uniform(350.0, 2400.0), 2) if is_completed else 0.0

            work_orders.append({
                "work_order_id": wo_id,
                "asset_id": cal["asset_id"],
                "order_type": "FAILED_CALIBRATION",
                "priority": "CRITICAL",
                "status": "COMPLETED" if is_completed else "IN_PROGRESS",
                "assigned_technician": rng.choice(TECHNICIANS),
                "creation_date": c_date,
                "scheduled_date": c_date + timedelta(days=1),
                "completion_date": comp_date,
                "downtime_hours": dt_hours,
                "cost": cost,
                "resolution_notes": "Instrument re-calibrated and re-certified." if is_completed else "Awaiting replacement sensor cartridge.",
                "created_at": c_date,
                "updated_at": comp_date or c_date
            })

    # 2. Orders for overdue assets
    for asset in assets:
        if asset["status"] == "ACTIVE" and asset["next_due_date"] and asset["next_due_date"] < sim_date:
            wo_id = f"WO-2026-{wo_seq:06d}"
            wo_seq += 1
            c_date = asset["next_due_date"]
            work_orders.append({
                "work_order_id": wo_id,
                "asset_id": asset["asset_id"],
                "order_type": "OVERDUE_CALIBRATION",
                "priority": "HIGH",
                "status": "OPEN",
                "assigned_technician": rng.choice(TECHNICIANS),
                "creation_date": c_date,
                "scheduled_date": c_date + timedelta(days=2),
                "completion_date": None,
                "downtime_hours": 0.0,
                "cost": 0.0,
                "resolution_notes": None,
                "created_at": c_date,
                "updated_at": c_date
            })

    # 3. Scheduled upcoming calibrations
    for asset in assets:
        if asset["status"] == "ACTIVE" and asset["next_due_date"] and sim_date <= asset["next_due_date"] <= (sim_date + timedelta(days=30)):
            if rng.random() < 0.6:  # 60% already have proactive work orders created
                wo_id = f"WO-2026-{wo_seq:06d}"
                wo_seq += 1
                c_date = sim_date - timedelta(days=rng.randint(1, 5))
                work_orders.append({
                    "work_order_id": wo_id,
                    "asset_id": asset["asset_id"],
                    "order_type": "UPCOMING_CALIBRATION",
                    "priority": "MEDIUM",
                    "status": "OPEN",
                    "assigned_technician": rng.choice(TECHNICIANS),
                    "creation_date": c_date,
                    "scheduled_date": asset["next_due_date"],
                    "completion_date": None,
                    "downtime_hours": 0.0,
                    "cost": 0.0,
                    "resolution_notes": None,
                    "created_at": c_date,
                    "updated_at": c_date
                })

    return work_orders

def generate_production_uses(
    target_count: int,
    assets: List[Dict[str, Any]],
    calibrations: List[Dict[str, Any]],
    certificates: List[Dict[str, Any]],
    work_orders: List[Dict[str, Any]],
    extensions: List[Dict[str, Any]],
    sim_date: datetime,
    rng: random.Random
) -> List[Dict[str, Any]]:
    """
    Generate realistic shopfloor production uses across lines, batches, and shifts.
    Every event is evaluated through the compliance gatekeeper engine.
    """
    production_uses = []
    
    # Pre-index calibrations and certificates for rapid lookup
    cal_by_asset = {}
    for c in sorted(calibrations, key=lambda x: x["calibration_date"]):
        cal_by_asset.setdefault(c["asset_id"], []).append(c)

    cert_by_asset = {}
    for cert in certificates:
        cert_by_asset[cert["asset_id"]] = cert

    ext_by_asset = {}
    for ext in extensions:
        if ext["status"] == "ACTIVE":
            ext_by_asset[ext["asset_id"]] = ext

    wo_by_asset = {}
    for wo in work_orders:
        wo_by_asset.setdefault(wo["asset_id"], []).append(wo)

    active_assets = [a for a in assets if a["status"] in ["ACTIVE", "IN_CALIBRATION"]]
    if not active_assets:
        active_assets = assets

    lines = [f"Line-{i:02d}" for i in range(1, 11)]
    start_year = datetime(REFERENCE_YEAR, 1, 1)

    batch_idx = 1
    # Distribute use events chronologically across the year up to sim_date
    total_days = max(1, (sim_date - start_year).days)

    for i in range(1, target_count + 1):
        asset = rng.choice(active_assets)
        asset_id = asset["asset_id"]

        day_offset = rng.randint(0, total_days)
        hour = rng.randint(6, 22)
        minute = rng.randint(0, 59)
        second = rng.randint(0, 59)
        use_time = start_year + timedelta(days=day_offset, hours=hour, minutes=minute, seconds=second)

        batch_id = f"{BATCH_PREFIX}{batch_idx:05d}"
        if i % 8 == 0:
            batch_idx += 1

        line = rng.choice(lines)
        operator_id = rng.choice(OPERATORS)

        # Retrieve latest calibration before use_time
        asset_cals = cal_by_asset.get(asset_id, [])
        prior_cals = [c for c in asset_cals if c["calibration_date"] <= use_time]
        latest_cal = prior_cals[-1] if prior_cals else None

        cert = cert_by_asset.get(asset_id)
        active_ext = ext_by_asset.get(asset_id)
        wos = wo_by_asset.get(asset_id, [])

        # Evaluate through compliance gatekeeper
        eval_result = evaluate_production_usage(
            asset=asset,
            usage_timestamp=use_time,
            latest_calibration=latest_cal,
            certificate=cert,
            active_work_orders=wos,
            active_extension=active_ext
        )

        time_str = use_time.strftime("%Y%m%d%H%M%S")
        usage_id = f"USE-{asset_id}-{time_str}-{i:06d}"

        production_uses.append({
            "usage_id": usage_id,
            "asset_id": asset_id,
            "usage_timestamp": use_time,
            "batch_id": batch_id,
            "production_line": line,
            "operator_id": operator_id,
            "decision": eval_result["decision"],
            "policy_applied": eval_result["policy_applied"],
            "reason": eval_result["reason"],
            "validation_passed": eval_result["validation_passed"],
            "created_at": use_time
        })

    return production_uses

def generate_alerts_and_audit(
    assets: List[Dict[str, Any]],
    calibrations: List[Dict[str, Any]],
    certificates: List[Dict[str, Any]],
    production_uses: List[Dict[str, Any]],
    work_orders: List[Dict[str, Any]],
    sim_date: datetime,
    rng: random.Random
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generate compliance alerts and immutable audit log records.
    """
    alerts = []
    audit_records = []
    alert_seq = 1
    aud_seq = 1

    # Alerts for failed calibrations
    for cal in calibrations:
        if cal["result"] == "FAIL":
            alerts.append({
                "alert_id": f"ALT-{alert_seq:06d}",
                "asset_id": cal["asset_id"],
                "alert_type": "FAILED_CALIBRATION",
                "severity": "CRITICAL",
                "message": f"Critical: Instrument {cal['asset_id']} failed calibration test {cal['calibration_id']}.",
                "status": "ACTIVE",
                "created_at": cal["calibration_date"],
                "acknowledged_at": None,
                "resolved_at": None
            })
            alert_seq += 1

    # Alerts for overdue assets
    for a in assets:
        if a["status"] == "ACTIVE" and a["next_due_date"] and a["next_due_date"] < sim_date:
            alerts.append({
                "alert_id": f"ALT-{alert_seq:06d}",
                "asset_id": a["asset_id"],
                "alert_type": "OVERDUE_CALIBRATION",
                "severity": "HIGH",
                "message": f"Warning: Instrument {a['asset_id']} is overdue for calibration since {a['next_due_date'].strftime('%Y-%m-%d')}.",
                "status": "ACTIVE",
                "created_at": a["next_due_date"],
                "acknowledged_at": None,
                "resolved_at": None
            })
            alert_seq += 1

    # Alerts for blocked/unauthorized production attempts
    for u in production_uses:
        if u["decision"] == "BLOCKED" and "expired" in u["reason"].lower():
            alerts.append({
                "alert_id": f"ALT-{alert_seq:06d}",
                "asset_id": u["asset_id"],
                "alert_type": "UNAUTHORIZED_USAGE",
                "severity": "CRITICAL",
                "message": f"Prohibited Usage Attempt: Operator attempted to use expired instrument {u['asset_id']} on {u['production_line']}.",
                "status": "ACTIVE",
                "created_at": u["usage_timestamp"],
                "acknowledged_at": None,
                "resolved_at": None
            })
            alert_seq += 1

    # Audit records for asset onboarding and key transitions
    for a in assets:
        audit_records.append({
            "audit_id": f"AUD-{aud_seq:06d}",
            "table_name": "assets",
            "record_id": a["asset_id"],
            "action": "INSERT",
            "actor": "System Automation Provisioner",
            "timestamp": a["commissioning_date"],
            "old_values_json": None,
            "new_values_json": f'{{"asset_id": "{a["asset_id"]}", "status": "{a["status"]}", "serial": "{a["serial_number"]}"}}',
            "reason": "Initial asset commissioning and registry registration."
        })
        aud_seq += 1

    return alerts, audit_records