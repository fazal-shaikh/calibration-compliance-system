-- =============================================================================
-- Enterprise Calibration Management & Compliance System
-- Database Schema (Portable: SQLite & PostgreSQL compatible)
-- =============================================================================

PRAGMA foreign_keys = ON;

-- 1. Supplier Table
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255),
    phone VARCHAR(64),
    address VARCHAR(500),
    is_accredited BOOLEAN NOT NULL DEFAULT 1,
    accreditation_number VARCHAR(128),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Instrument Type Table
CREATE TABLE IF NOT EXISTS instrument_types (
    type_id VARCHAR(32) PRIMARY KEY,
    category VARCHAR(64) NOT NULL,
    model_name VARCHAR(255) NOT NULL,
    manufacturer VARCHAR(255) NOT NULL,
    measurement_range VARCHAR(128) NOT NULL,
    default_interval_days INTEGER NOT NULL DEFAULT 365,
    default_tolerance FLOAT NOT NULL DEFAULT 0.05,
    unit_of_measure VARCHAR(32) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Calibration Plan Table
CREATE TABLE IF NOT EXISTS calibration_plans (
    plan_id VARCHAR(32) PRIMARY KEY,
    type_id VARCHAR(32) NOT NULL,
    name VARCHAR(255) NOT NULL,
    interval_days INTEGER NOT NULL,
    tolerance FLOAT NOT NULL,
    mandatory_certificate BOOLEAN NOT NULL DEFAULT 1,
    standard_operating_procedure VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (type_id) REFERENCES instrument_types(type_id) ON DELETE RESTRICT
);

-- 4. Asset (Physical Instrument) Table
CREATE TABLE IF NOT EXISTS assets (
    asset_id VARCHAR(32) PRIMARY KEY,
    serial_number VARCHAR(128) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    type_id VARCHAR(32) NOT NULL,
    plan_id VARCHAR(32) NOT NULL,
    supplier_id VARCHAR(32) NOT NULL,
    department VARCHAR(128) NOT NULL,
    location VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL, -- ACTIVE, IN_CALIBRATION, OUT_OF_SERVICE, RETIRED, QUARANTINED
    commissioning_date TIMESTAMP NOT NULL,
    last_calibration_date TIMESTAMP,
    next_due_date TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (type_id) REFERENCES instrument_types(type_id) ON DELETE RESTRICT,
    FOREIGN KEY (plan_id) REFERENCES calibration_plans(plan_id) ON DELETE RESTRICT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE RESTRICT
);

-- 5. Calibration Event Table
CREATE TABLE IF NOT EXISTS calibration_events (
    calibration_id VARCHAR(64) PRIMARY KEY,
    asset_id VARCHAR(32) NOT NULL,
    plan_id VARCHAR(32) NOT NULL,
    calibration_date TIMESTAMP NOT NULL,
    technician VARCHAR(128) NOT NULL,
    measured_value FLOAT NOT NULL,
    reference_value FLOAT NOT NULL,
    tolerance FLOAT NOT NULL,
    deviation FLOAT NOT NULL,
    result VARCHAR(16) NOT NULL, -- PASS, FAIL
    temperature_celsius FLOAT,
    humidity_percent FLOAT,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE RESTRICT,
    FOREIGN KEY (plan_id) REFERENCES calibration_plans(plan_id) ON DELETE RESTRICT
);

-- 6. Certificate Table
CREATE TABLE IF NOT EXISTS certificates (
    certificate_id VARCHAR(64) PRIMARY KEY,
    certificate_number VARCHAR(128) NOT NULL UNIQUE,
    calibration_id VARCHAR(64) NOT NULL,
    asset_id VARCHAR(32) NOT NULL,
    issue_date TIMESTAMP NOT NULL,
    expiry_date TIMESTAMP NOT NULL,
    verification_status VARCHAR(32) NOT NULL, -- VALID, EXPIRED, REVOKED, MISMATCHED
    issuer_name VARCHAR(255) NOT NULL,
    digital_signature_hash VARCHAR(128),
    file_path VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (calibration_id) REFERENCES calibration_events(calibration_id) ON DELETE RESTRICT,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE RESTRICT
);

-- 7. Work Order Table
CREATE TABLE IF NOT EXISTS work_orders (
    work_order_id VARCHAR(64) PRIMARY KEY,
    asset_id VARCHAR(32) NOT NULL,
    order_type VARCHAR(64) NOT NULL, -- UPCOMING_CALIBRATION, OVERDUE_CALIBRATION, FAILED_CALIBRATION, CORRECTIVE_MAINTENANCE, INVESTIGATION
    priority VARCHAR(16) NOT NULL, -- LOW, MEDIUM, HIGH, CRITICAL
    status VARCHAR(32) NOT NULL, -- OPEN, IN_PROGRESS, PENDING_REVIEW, COMPLETED, CANCELLED
    assigned_technician VARCHAR(128),
    creation_date TIMESTAMP NOT NULL,
    scheduled_date TIMESTAMP,
    completion_date TIMESTAMP,
    downtime_hours FLOAT NOT NULL DEFAULT 0.0,
    cost FLOAT NOT NULL DEFAULT 0.0,
    resolution_notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE RESTRICT
);

-- 8. Production Use Table
CREATE TABLE IF NOT EXISTS production_uses (
    usage_id VARCHAR(128) PRIMARY KEY,
    asset_id VARCHAR(32) NOT NULL,
    usage_timestamp TIMESTAMP NOT NULL,
    batch_id VARCHAR(128) NOT NULL,
    production_line VARCHAR(64) NOT NULL,
    operator_id VARCHAR(64) NOT NULL,
    decision VARCHAR(32) NOT NULL, -- ALLOWED, BLOCKED, ALLOWED_WITH_EXCEPTION
    policy_applied VARCHAR(64) NOT NULL,
    reason TEXT NOT NULL,
    validation_passed BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE RESTRICT
);

-- 9. Alert Table
CREATE TABLE IF NOT EXISTS alerts (
    alert_id VARCHAR(64) PRIMARY KEY,
    asset_id VARCHAR(32),
    alert_type VARCHAR(64) NOT NULL, -- UPCOMING_CALIBRATION, OVERDUE_CALIBRATION, FAILED_CALIBRATION, MISSING_CERTIFICATE, EXPIRED_CERTIFICATE, UNAUTHORIZED_USAGE, MISSING_IMPACT_ASSESSMENT, EXTENSION_EXPIRY
    severity VARCHAR(16) NOT NULL, -- LOW, MEDIUM, HIGH, CRITICAL
    message TEXT NOT NULL,
    status VARCHAR(32) NOT NULL, -- ACTIVE, ACKNOWLEDGED, RESOLVED, DISMISSED
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE SET NULL
);

-- 10. Audit Record Table (Immutable Append-only)
CREATE TABLE IF NOT EXISTS audit_records (
    audit_id VARCHAR(64) PRIMARY KEY,
    table_name VARCHAR(64) NOT NULL,
    record_id VARCHAR(128) NOT NULL,
    action VARCHAR(16) NOT NULL, -- INSERT, UPDATE, DELETE
    actor VARCHAR(128) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    old_values_json TEXT,
    new_values_json TEXT,
    reason VARCHAR(500)
);

-- 11. Supporting Entity: Corrective Action (CAPA)
CREATE TABLE IF NOT EXISTS corrective_actions (
    corrective_action_id VARCHAR(64) PRIMARY KEY,
    calibration_id VARCHAR(64) NOT NULL,
    asset_id VARCHAR(32) NOT NULL,
    work_order_id VARCHAR(64),
    status VARCHAR(32) NOT NULL, -- OPEN, IN_PROGRESS, VERIFIED, CLOSED
    root_cause TEXT,
    containment_action TEXT,
    preventive_action TEXT,
    assigned_to VARCHAR(128),
    target_date TIMESTAMP,
    closed_date TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (calibration_id) REFERENCES calibration_events(calibration_id) ON DELETE RESTRICT,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE RESTRICT,
    FOREIGN KEY (work_order_id) REFERENCES work_orders(work_order_id) ON DELETE SET NULL
);

-- 12. Supporting Entity: Impact Assessment
CREATE TABLE IF NOT EXISTS impact_assessments (
    assessment_id VARCHAR(64) PRIMARY KEY,
    calibration_id VARCHAR(64) NOT NULL,
    asset_id VARCHAR(32) NOT NULL,
    investigation_status VARCHAR(32) NOT NULL, -- OPEN, IN_INVESTIGATION, CONCLUDED, DISPOSITIONED
    risk_level VARCHAR(16) NOT NULL, -- LOW, MEDIUM, HIGH, CRITICAL
    affected_batches_count INTEGER NOT NULL DEFAULT 0,
    affected_usage_events_count INTEGER NOT NULL DEFAULT 0,
    investigation_summary TEXT,
    disposition VARCHAR(255),
    assessor VARCHAR(128),
    assessment_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_date TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (calibration_id) REFERENCES calibration_events(calibration_id) ON DELETE RESTRICT,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE RESTRICT
);

-- 13. Supporting Entity: Calibration Extension
CREATE TABLE IF NOT EXISTS calibration_extensions (
    extension_id VARCHAR(64) PRIMARY KEY,
    asset_id VARCHAR(32) NOT NULL,
    original_due_date TIMESTAMP NOT NULL,
    extended_due_date TIMESTAMP NOT NULL,
    approved_by VARCHAR(128) NOT NULL,
    approval_date TIMESTAMP NOT NULL,
    justification TEXT NOT NULL,
    status VARCHAR(32) NOT NULL, -- ACTIVE, EXPIRED, SUPERSEDED, REVOKED
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE RESTRICT
);

-- 14. Supporting Bridge: Work Order Assets
CREATE TABLE IF NOT EXISTS work_order_assets (
    id VARCHAR(64) PRIMARY KEY,
    work_order_id VARCHAR(64) NOT NULL,
    asset_id VARCHAR(32) NOT NULL,
    role VARCHAR(64) NOT NULL DEFAULT 'PRIMARY', -- PRIMARY, REFERENCE_STANDARD, VERIFICATION_TARGET
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_order_id) REFERENCES work_orders(work_order_id) ON DELETE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
);

-- Indexes for high-throughput queries and integrity
CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status);
CREATE INDEX IF NOT EXISTS idx_assets_due_date ON assets(next_due_date);
CREATE INDEX IF NOT EXISTS idx_cal_asset_date ON calibration_events(asset_id, calibration_date);
CREATE INDEX IF NOT EXISTS idx_cert_asset ON certificates(asset_id);
CREATE INDEX IF NOT EXISTS idx_cert_cal ON certificates(calibration_id);
CREATE INDEX IF NOT EXISTS idx_wo_status ON work_orders(status);
CREATE INDEX IF NOT EXISTS idx_wo_asset ON work_orders(asset_id);
CREATE INDEX IF NOT EXISTS idx_use_asset_time ON production_uses(asset_id, usage_timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(status, severity);
CREATE INDEX IF NOT EXISTS idx_impact_cal ON impact_assessments(calibration_id);