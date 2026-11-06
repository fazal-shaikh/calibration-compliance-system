# Source Manifest & Data Provenance

## 1. Ethical & Synthetic Data Disclosure
> [!IMPORTANT]
> **Synthetic Data Statement**: All data utilized, generated, stored, and exported within this project is **100% synthetically generated** using deterministic algorithms seeded with `20261022`. No real-world manufacturing plant, proprietary equipment, commercial serial numbers, or personally identifiable information (PII) are represented.

---

## 2. Source Code & Artifact Inventory

### Application & Configuration
| File Path | Description | Role / Responsibility |
| :--- | :--- | :--- |
| `app.py` | Main Streamlit Application | Multi-page routing, layout configuration, session lifecycle |
| `requirements.txt` | Python Dependencies | Project package specifications (Pandas, SQLAlchemy, Streamlit, etc.) |
| `pytest.ini` | Pytest Configuration | Pythonpath resolution, test directory mapping, test runner flags |
| `.gitignore` | Git Exclusions | Excludes SQLite databases, caches, logs, and temporary virtual environments |
| `config/settings.py` | System Configuration | Path constants, seed `20261022`, scale configurations, tolerances |

### Database Layer
| File Path | Description | Role / Responsibility |
| :--- | :--- | :--- |
| `database/connection.py` | Connection Manager | SQLite/PostgreSQL connection pooling, WAL mode, foreign key pragma |
| `database/models.py` | Declarative ORM Models | 10 required core entities + 4 supporting entities with relationships |
| `database/schema.sql` | Relational DDL Script | ANSI SQL schema definition with indexes and constraints |
| `database/seed.py` | Database Seeder | Programmatic wrapper to initialize database from generator |
| `database/seed.sql` | Portable SQL Inserts | SQL statements for master data and baseline assets |

### Generator Pipeline
| File Path | Description | Role / Responsibility |
| :--- | :--- | :--- |
| `generator/master_data.py` | Master Data Generator | Generates Suppliers, InstrumentTypes, CalibrationPlans, Assets |
| `generator/transaction_data.py` | Transaction Generator | Generates CalibrationEvents, Certificates, WorkOrders, ProductionUses |
| `generator/anomaly_injection.py`| Anomaly Injection Engine | Injects 4 required edge cases into controlled subsets |
| `generator/ground_truth.py` | Ground Truth Registry | Saves and loads isolated `ground_truth.csv` |
| `generator/generate.py` | Pipeline CLI Orchestrator | Parameterized pipeline (`--scale starter/full`, `--seed 20261022`) |

### Domain Business Logic
| File Path | Description | Role / Responsibility |
| :--- | :--- | :--- |
| `business_logic/calibration.py` | Metrology Math | Deviation formula, tolerance check, next due date calculation |
| `business_logic/scheduling.py` | Scheduling Engine | Overdue checking, upcoming window forecast, extension checks |
| `business_logic/production_validation.py` | Shopfloor Gatekeeper | 8-point compliance check determining ALLOWED / BLOCKED |
| `business_logic/certificates.py` | Certificate Reconciler | Cross-checks certificate asset references and expiry dates |
| `business_logic/work_orders.py` | Maintenance Management | Dispatching work orders, status tracking, MTTR calculation |
| `business_logic/corrective_actions.py` | Failure Containment | Retrospective lot tracing between last valid test and failure |
| `business_logic/alerts.py` | Alert Engine | Standardized compliance alerts and severity assignment |

### Application Services Layer
| File Path | Description | Role / Responsibility |
| :--- | :--- | :--- |
| `services/instrument_service.py` | Instrument Service | CRUD operations, status updates, emergency extension grants |
| `services/calibration_service.py` | Calibration Service | Test recording, certificate issuance, failure quarantining |
| `services/production_service.py` | Production Service | Live gatekeeper validation and usage event persistence |
| `services/audit_service.py` | Audit Service | Centralized immutable audit logging |

### Dashboard (Streamlit & Plotly)
| File Path | Description | Role / Responsibility |
| :--- | :--- | :--- |
| `dashboard/overview.py` | Executive Overview | High-level KPI cards, status distribution, outcome charts |
| `dashboard/instruments.py` | Instrument Registry | Multi-criteria filtering, lifecycle inspection, status transitions |
| `dashboard/calibration.py` | Calibration Management | Measurement deviation scatter plots, certificates, new test form |
| `dashboard/production.py` | Production & Gatekeeper | Live shopfloor gatekeeper simulator and transaction logs |
| `dashboard/work_orders.py` | Work Orders & CAPA | Open/completed maintenance orders, downtime, CAPA, lot tracing |
| `dashboard/alerts.py` | Compliance Alerts | Active hazards list, acknowledgement & resolution actions |
| `dashboard/audit.py` | Audit Ledger | Immutable transaction history, JSON old/new diff inspector |
| `dashboard/data_quality.py` | Data Quality & Benchmarks | Quality audit cards, independent anomaly detection vs ground truth |

### Quality, Verification & Benchmarking
| File Path | Description | Role / Responsibility |
| :--- | :--- | :--- |
| `validation/integrity.py` | Relational Verifier | Primary key uniqueness, foreign key consistency, enum validation |
| `validation/lifecycle.py` | Lifecycle Verifier | Validates state transitions (quarantine, completed orders) |
| `validation/evaluation.py` | Metrics & Anomaly Engine| Evaluates 12 KPIs, independent anomaly detection, confusion matrix |
| `validation/reproducibility.py`| Reproducibility Verifier| Dual-run pipeline comparator with SHA-256 hash checks |
| `validation/data_quality.py` | Validation Report CLI | Aggregates all audits and writes `docs/validation_report.md` |

### Automated Test Suite (Pytest)
| File Path | Description | Role / Responsibility |
| :--- | :--- | :--- |
| `tests/conftest.py` | Pytest Fixtures | Root sys.path configuration |
| `tests/test_generator.py` | Generator Tests | Deterministic ID format validation, master data integrity |
| `tests/test_calibration.py` | Calibration Tests | Deviation math, tolerance boundary tests, due date calculation |
| `tests/test_production.py` | Gatekeeper Tests | All 8 gates (positive, negative, exception, blocking WOs) |
| `tests/test_certificates.py` | Certificate Tests | Linkage, mismatch detection, expired certificate detection |
| `tests/test_corrective_actions.py`| CAPA & Tracing Tests | Retrospective production lot tracing, failure package creation |
| `tests/test_integrity.py` | Integrity Tests | Zero duplicate PKs, zero orphan FKs, valid enums, valid dates |
| `tests/test_anomalies.py` | Anomaly Tests | Independent detection vs ground truth (Precision & Recall >= 0.95) |
| `tests/test_reproducibility.py`| Reproducibility Tests | Seed `20261022` bit-for-bit identity across multiple executions |