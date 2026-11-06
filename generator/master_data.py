"""
Master Data Generator
Generates deterministic Suppliers, InstrumentTypes, CalibrationPlans, and Assets.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from config.settings import SEED, REFERENCE_YEAR, CATEGORY_TOLERANCES

DEPARTMENTS = [
    "Quality Assurance", "Machining", "Assembly", 
    "Thermal Processing", "Packaging", "Chemical Lab"
]

LOCATIONS = [
    f"Line-0{i}" for i in range(1, 10)
] + [f"Line-{i}" for i in range(10, 16)] + [
    "Clean-Room-1", "Metrology-Lab", "Furnace-Area", "CNC-Shop"
]

INSTRUMENT_SPECS = [
    # Pressure
    ("Pressure", "Digital Pressure Gauge DPG-100", "Sensirion Metrology", "0-100 bar", 180, 0.05, "bar"),
    ("Pressure", "Differential Pressure Transmitter PT-50", "Yokogawa", "0-50 bar", 365, 0.02, "bar"),
    ("Pressure", "Vacuum Sensor VS-10", "Pfeiffer Vacuum", "-1 to 0 bar", 180, 0.01, "bar"),
    # Temperature
    ("Temperature", "Pt100 RTD Probe TempMaster", "Fluke Precision", "-50 to 250 C", 180, 0.2, "deg C"),
    ("Temperature", "Thermocouple Type K HighTemp", "Omega Engineering", "0 to 1200 C", 90, 1.0, "deg C"),
    ("Temperature", "Infrared Pyrometer OptiPoint", "Raytek Systems", "100 to 800 C", 180, 0.5, "deg C"),
    # Flow
    ("Flow", "Coriolis Mass Flowmeter Promass 300", "Endress+Hauser", "0-500 kg/h", 365, 0.1, "kg/h"),
    ("Flow", "Electromagnetic Flowmeter Mag-50", "KROHNE", "0-1000 L/min", 365, 0.5, "L/min"),
    # Electrical
    ("Electrical", "Precision Digital Multimeter 8.5 Digit", "Keysight Technologies", "0-1000 V", 365, 0.005, "V"),
    ("Electrical", "Current Calibrator Source 24mA", "AMETEK", "0-24 mA", 180, 0.01, "mA"),
    # Dimensional
    ("Dimensional", "Digital Micrometer 0-25mm", "Mitutoyo", "0-25 mm", 180, 0.002, "mm"),
    ("Dimensional", "Vernier Caliper High-Accuracy 300mm", "Fowler", "0-300 mm", 365, 0.01, "mm"),
    # Weighing
    ("Weighing", "Analytical Balance XPR-205", "Mettler Toledo", "0-220 g", 180, 0.0001, "g"),
    ("Weighing", "Heavy Duty Platform Scale 1000kg", "Avery Weigh-Tronix", "0-1000 kg", 365, 0.05, "kg")
]

SUPPLIERS_DATA = [
    ("SUP-001", "Fluke Precision Metrology Labs", "support@fluke-metrology.com", "+1-800-443-5853", "Everett, WA, USA", True, "ACCRED-ISO17025-001"),
    ("SUP-002", "Endress+Hauser Metrology Services", "service@endress.com", "+41-61-715-7700", "Reinach, Switzerland", True, "ACCRED-ISO17025-002"),
    ("SUP-003", "Mitutoyo Standards Laboratory", "calibrations@mitutoyo.co.jp", "+81-44-813-8201", "Kawasaki, Japan", True, "ACCRED-ISO17025-003"),
    ("SUP-004", "Mettler Toledo Metrology Division", "metrology@mt.com", "+1-800-638-8537", "Columbus, OH, USA", True, "ACCRED-ISO17025-004"),
    ("SUP-005", "Yokogawa Technical Calibration Center", "calibration@yokogawa.com", "+81-422-52-5555", "Tokyo, Japan", True, "ACCRED-ISO17025-005"),
    ("SUP-006", "Keysight Metrology Services", "service@keysight.com", "+1-800-829-4444", "Santa Rosa, CA, USA", True, "ACCRED-ISO17025-006"),
    ("SUP-007", "Omega Calibration Laboratory", "service@omega.com", "+1-888-826-6342", "Norwalk, CT, USA", True, "ACCRED-ISO17025-007"),
    ("SUP-008", "Avery Weigh-Tronix Metrology", "service@averyweigh-tronix.com", "+44-121-568-1660", "Birmingham, UK", True, "ACCRED-ISO17025-008"),
    ("SUP-009", "National Quality Metrology Center", "contact@nqmc-labs.org", "+1-202-555-0199", "Gaithersburg, MD, USA", True, "ACCRED-ISO17025-009"),
    ("SUP-010", "EuroCal Metrology Laboratories", "info@eurocal-labs.eu", "+49-30-555-0122", "Berlin, Germany", True, "ACCRED-ISO17025-010")
]

def generate_suppliers() -> List[Dict[str, Any]]:
    """Generate master supplier records."""
    suppliers = []
    base_date = datetime(REFERENCE_YEAR - 2, 1, 15, 8, 0, 0)
    for s_id, name, email, phone, addr, accredited, accred_num in SUPPLIERS_DATA:
        suppliers.append({
            "supplier_id": s_id,
            "name": name,
            "contact_email": email,
            "phone": phone,
            "address": addr,
            "is_accredited": accredited,
            "accreditation_number": accred_num,
            "created_at": base_date
        })
    return suppliers

def generate_instrument_types() -> List[Dict[str, Any]]:
    """Generate instrument types catalog."""
    types = []
    base_date = datetime(REFERENCE_YEAR - 2, 1, 15, 8, 30, 0)
    for idx, (cat, model, mfr, m_range, interval, tol, uom) in enumerate(INSTRUMENT_SPECS, 1):
        type_id = f"TYP-{idx:03d}"
        types.append({
            "type_id": type_id,
            "category": cat,
            "model_name": model,
            "manufacturer": mfr,
            "measurement_range": m_range,
            "default_interval_days": interval,
            "default_tolerance": tol,
            "unit_of_measure": uom,
            "created_at": base_date
        })
    return types

def generate_calibration_plans(instrument_types: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate calibration plans linked to instrument types."""
    plans = []
    base_date = datetime(REFERENCE_YEAR - 2, 1, 15, 9, 0, 0)
    for idx, it in enumerate(instrument_types, 1):
        plan_id = f"PLAN-{idx:03d}"
        plans.append({
            "plan_id": plan_id,
            "type_id": it["type_id"],
            "name": f"Standard Calibration Procedure for {it['model_name']}",
            "interval_days": it["default_interval_days"],
            "tolerance": it["default_tolerance"],
            "mandatory_certificate": True,
            "standard_operating_procedure": f"SOP-CAL-{it['category'].upper()[:4]}-{idx:02d}",
            "created_at": base_date
        })
    return plans

def generate_assets(
    count: int,
    instrument_types: List[Dict[str, Any]],
    calibration_plans: List[Dict[str, Any]],
    suppliers: List[Dict[str, Any]],
    rng: random.Random
) -> List[Dict[str, Any]]:
    """
    Generate physical instrument assets with deterministic IDs AST-000001 ...
    Assigned realistic operational statuses and baseline commissioning dates.
    """
    assets = []
    type_plan_map = {p["type_id"]: p["plan_id"] for p in calibration_plans}
    supplier_ids = [s["supplier_id"] for s in suppliers]

    # Status distribution: ~88% ACTIVE, ~5% IN_CALIBRATION, ~3% OUT_OF_SERVICE, ~2% QUARANTINED, ~2% RETIRED
    status_choices = ["ACTIVE", "IN_CALIBRATION", "OUT_OF_SERVICE", "QUARANTINED", "RETIRED"]
    status_weights = [0.88, 0.05, 0.03, 0.02, 0.02]

    base_comm_date = datetime(REFERENCE_YEAR - 3, 1, 1)

    for i in range(1, count + 1):
        asset_id = f"AST-{i:06d}"
        itype = rng.choice(instrument_types)
        type_id = itype["type_id"]
        plan_id = type_plan_map[type_id]
        supplier_id = rng.choice(supplier_ids)

        dept = rng.choice(DEPARTMENTS)
        loc = rng.choice(LOCATIONS)
        status = rng.choices(status_choices, weights=status_weights)[0]

        # Commissioning date between 3 years ago and 6 months ago
        days_offset = rng.randint(0, 900)
        comm_date = base_comm_date + timedelta(days=days_offset)

        assets.append({
            "asset_id": asset_id,
            "serial_number": f"SN-{itype['category'][:3].upper()}-{i:06d}-{rng.randint(1000, 9999)}",
            "name": f"{itype['model_name']} ({loc})",
            "type_id": type_id,
            "plan_id": plan_id,
            "supplier_id": supplier_id,
            "department": dept,
            "location": loc,
            "status": status,
            "commissioning_date": comm_date,
            "last_calibration_date": None,  # Will be calculated and set from calibration events
            "next_due_date": None,          # Will be calculated from latest valid calibration
            "created_at": comm_date,
            "updated_at": comm_date
        })

    return assets