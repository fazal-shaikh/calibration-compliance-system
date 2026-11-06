"""
Application Configuration and Settings
Supports portable database configuration, environment overrides, and system constants.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"
EXPORTS_DIR = DATA_DIR / "exports"
LOGS_DIR = BASE_DIR / "logs"
DOCS_DIR = BASE_DIR / "docs"

# Ensure runtime directories exist
for p in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, GROUND_TRUTH_DIR, EXPORTS_DIR, LOGS_DIR, DOCS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# Database Configuration (Portable: SQLite default, overridable to PostgreSQL)
DEFAULT_DB_PATH = DATA_DIR / "calibration.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

# Seed & Reproducibility Settings
SEED = 20261022
REFERENCE_YEAR = 2026

# Scale Configurations
SCALE_CONFIGS = {
    "starter": {
        "assets_count": 50,
        "calibration_events_count": 150,
        "production_use_count": 1500,
        "history_days": 365
    },
    "full": {
        "assets_count": 2000,
        "calibration_events_count": 5000,
        "production_use_count": 100000,
        "history_days": 365
    }
}

# Calibration Policy Thresholds
UPCOMING_WINDOW_DAYS = 30  # Days before due date to flag upcoming calibration
MAX_EXTENSION_DAYS = 30    # Maximum allowable emergency extension period
CALIBRATION_GRACE_PERIOD_DAYS = 0  # Zero tolerance: strictly overdue once due_date passes

# Tolerance Bands per category
CATEGORY_TOLERANCES = {
    "Pressure": 0.05,        # +/- 0.05 bar/psi
    "Temperature": 0.5,      # +/- 0.5 deg C
    "Flow": 0.1,             # +/- 0.1 L/min
    "Electrical": 0.01,      # +/- 0.01 V/mA
    "Dimensional": 0.005,    # +/- 0.005 mm
    "Weighing": 0.02         # +/- 0.02 g/kg
}

# Logging Configuration
LOG_FILE = LOGS_DIR / "calibration_system.log"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")