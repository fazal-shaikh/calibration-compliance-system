"""
Deterministic Synthetic Data Pipeline Orchestrator
Coordinates generation of all 10 core entities and 4 supporting entities,
injects edge cases, exports CSV/JSON files, and seeds the relational database.
"""

import argparse
import json
import logging
import random
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import (
    SEED, REFERENCE_YEAR, SCALE_CONFIGS, EXPORTS_DIR,
    PROCESSED_DATA_DIR, RAW_DATA_DIR, GROUND_TRUTH_DIR
)
from database.connection import init_db, reset_db, SessionLocal
from database.models import (
    Supplier, InstrumentType, CalibrationPlan, Asset,
    CalibrationEvent, Certificate, WorkOrder, ProductionUse,
    Alert, AuditRecord, CorrectiveAction, ImpactAssessment,
    CalibrationExtension, WorkOrderAsset
)
from generator.master_data import (
    generate_suppliers, generate_instrument_types,
    generate_calibration_plans, generate_assets
)
from generator.transaction_data import (
    generate_calibration_and_certificates, generate_work_orders,
    generate_production_uses, generate_alerts_and_audit
)
from generator.anomaly_injection import inject_anomalies

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def run_pipeline(scale: str = "starter", seed: int = SEED, seed_database: bool = True, export_files: bool = True):
    """Execute complete deterministic data generation pipeline."""
    logger.info(f"Starting synthetic data generation pipeline (scale={scale}, seed={seed})")
    rng = random.Random(seed)
    cfg = SCALE_CONFIGS.get(scale, SCALE_CONFIGS["starter"])
    
    sim_date = datetime(REFERENCE_YEAR, 11, 1, 17, 0, 0)

    # 1. Generate Master Data
    logger.info("Generating Suppliers, Instrument Types, Calibration Plans, and Assets...")
    suppliers = generate_suppliers()
    types = generate_instrument_types()
    plans = generate_calibration_plans(types)
    assets = generate_assets(cfg["assets_count"], types, plans, suppliers, rng)

    # 2. Emergency Extensions (Realistic ~2% of assets)
    extensions = []
    ext_seq = 1
    for a in assets[:max(2, int(len(assets) * 0.02))]:
        orig_due = sim_date - random.Random(seed).choice([datetime(REFERENCE_YEAR, 10, 15) - datetime(REFERENCE_YEAR, 10, 1)])
        ext_due = sim_date + random.Random(seed).choice([datetime(REFERENCE_YEAR, 11, 15) - datetime(REFERENCE_YEAR, 11, 1)])
        extensions.append({
            "extension_id": f"EXT-2026-{ext_seq:06d}",
            "asset_id": a["asset_id"],
            "original_due_date": sim_date - random.Random(seed).choice([datetime(REFERENCE_YEAR, 10, 15) - datetime(REFERENCE_YEAR, 10, 1)]),
            "extended_due_date": sim_date + random.Random(seed).choice([datetime(REFERENCE_YEAR, 11, 15) - datetime(REFERENCE_YEAR, 11, 1)]),
            "approved_by": "Dr. Eleanor Vance (Director of Quality)",
            "approval_date": sim_date - random.Random(seed).choice([datetime(REFERENCE_YEAR, 10, 15) - datetime(REFERENCE_YEAR, 10, 1)]),
            "justification": "Critical production run pending scheduled weekend calibration turnaround.",
            "status": "ACTIVE",
            "created_at": sim_date - random.Random(seed).choice([datetime(REFERENCE_YEAR, 10, 15) - datetime(REFERENCE_YEAR, 10, 1)])
        })
        ext_seq += 1

    # 3. Generate Calibrations, Certificates, CAPA, and Impact Assessments
    logger.info(f"Generating {cfg['calibration_events_count']} Calibration Events and Certificates...")
    calibrations, certificates, corrective_actions, impact_assessments = generate_calibration_and_certificates(
        calibration_count=cfg["calibration_events_count"],
        assets=assets,
        plans=plans,
        suppliers=suppliers,
        rng=rng
    )

    # 4. Generate Work Orders
    logger.info("Generating Work Orders...")
    work_orders = generate_work_orders(assets, calibrations, sim_date, rng)

    # 5. Generate Production Uses
    logger.info(f"Generating {cfg['production_use_count']} Production Use events...")
    production_uses = generate_production_uses(
        target_count=cfg["production_use_count"],
        assets=assets,
        calibrations=calibrations,
        certificates=certificates,
        work_orders=work_orders,
        extensions=extensions,
        sim_date=sim_date,
        rng=rng
    )

    # 6. Generate Alerts and Audit Records
    logger.info("Generating Alerts and Audit Records...")
    alerts, audit_records = generate_alerts_and_audit(
        assets, calibrations, certificates, production_uses, work_orders, sim_date, rng
    )

    # 7. Inject Controlled Edge Cases & Register Ground Truth
    logger.info("Injecting 4 required compliance anomalies and saving ground truth...")
    gt_records, _ = inject_anomalies(
        assets=assets,
        plans=plans,
        calibrations=calibrations,
        certificates=certificates,
        production_uses=production_uses,
        impact_assessments=impact_assessments,
        corrective_actions=corrective_actions,
        extensions=extensions,
        sim_date=sim_date,
        rng=rng
    )

    datasets = {
        "suppliers": suppliers,
        "instrument_types": types,
        "calibration_plans": plans,
        "assets": assets,
        "calibration_events": calibrations,
        "certificates": certificates,
        "work_orders": work_orders,
        "production_uses": production_uses,
        "alerts": alerts,
        "audit_records": audit_records,
        "corrective_actions": corrective_actions,
        "impact_assessments": impact_assessments,
        "calibration_extensions": extensions
    }

    # 8. Export to CSV & JSON
    if export_files:
        logger.info(f"Exporting datasets to {EXPORTS_DIR}...")
        for name, records in datasets.items():
            csv_path = EXPORTS_DIR / f"{name}.csv"
            json_path = EXPORTS_DIR / f"{name}.json"

            if records:
                import pandas as pd
                df = pd.DataFrame(records)
                df.to_csv(csv_path, index=False)
                df.to_json(json_path, orient="records", date_format="iso", indent=2)

    # 9. Seed Database
    if seed_database:
        logger.info("Seeding relational database tables...")
        reset_db()
        db = SessionLocal()
        try:
            db.bulk_insert_mappings(Supplier, suppliers)
            db.bulk_insert_mappings(InstrumentType, types)
            db.bulk_insert_mappings(CalibrationPlan, plans)
            db.bulk_insert_mappings(Asset, assets)
            db.bulk_insert_mappings(CalibrationEvent, calibrations)
            db.bulk_insert_mappings(Certificate, certificates)
            db.bulk_insert_mappings(WorkOrder, work_orders)
            db.bulk_insert_mappings(ProductionUse, production_uses)
            db.bulk_insert_mappings(Alert, alerts)
            db.bulk_insert_mappings(AuditRecord, audit_records)
            db.bulk_insert_mappings(CorrectiveAction, corrective_actions)
            db.bulk_insert_mappings(ImpactAssessment, impact_assessments)
            db.bulk_insert_mappings(CalibrationExtension, extensions)
            db.commit()
            logger.info("Database seeding completed successfully.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error seeding database: {e}")
            raise
        finally:
            db.close()

    summary = {name: len(recs) for name, recs in datasets.items()}
    summary["ground_truth_anomalies"] = len(gt_records)
    logger.info(f"Generation pipeline finished. Record counts: {summary}")
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic Synthetic Data Generator")
    parser.add_argument("--scale", choices=["starter", "full"], default="starter", help="Dataset scale")
    parser.add_argument("--seed", type=int, default=SEED, help="Random seed for reproducibility")
    parser.add_argument("--no-db", action="store_true", help="Skip database seeding")
    parser.add_argument("--no-export", action="store_true", help="Skip file export")
    args = parser.parse_args()

    run_pipeline(
        scale=args.scale,
        seed=args.seed,
        seed_database=not args.no_db,
        export_files=not args.no_export
    )