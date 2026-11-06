"""
Tests for Data Generator and Deterministic ID Schemes
"""

import re
import pytest
import random
from datetime import datetime
from config.settings import SEED
from generator.master_data import (
    generate_suppliers, generate_instrument_types,
    generate_calibration_plans, generate_assets
)

def test_deterministic_id_conventions():
    """Verify that generated IDs adhere strictly to required regex patterns."""
    rng = random.Random(SEED)
    suppliers = generate_suppliers()
    types = generate_instrument_types()
    plans = generate_calibration_plans(types)
    assets = generate_assets(10, types, plans, suppliers, rng)

    # Asset ID: AST-000001
    for a in assets:
        assert re.match(r"^AST-\d{6}$", a["asset_id"]), f"Invalid asset_id {a['asset_id']}"
        assert a["serial_number"].startswith("SN-")

def test_master_data_referential_integrity():
    """Verify generated master data sets contain valid parent IDs."""
    suppliers = generate_suppliers()
    types = generate_instrument_types()
    plans = generate_calibration_plans(types)

    type_ids = {t["type_id"] for t in types}
    supplier_ids = {s["supplier_id"] for s in suppliers}

    for p in plans:
        assert p["type_id"] in type_ids, f"Plan references unknown type {p['type_id']}"
        assert p["interval_days"] in [90, 180, 365, 730]
        assert p["tolerance"] > 0.0

    for s in suppliers:
        assert s["supplier_id"].startswith("SUP-")
        assert len(s["name"]) > 2