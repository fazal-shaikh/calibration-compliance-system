# System Architecture: Enterprise Calibration & Compliance System

## 1. Architectural Overview & Design Principles

The Enterprise Calibration & Compliance System is an end-to-end, multi-tier industrial software platform designed to guarantee measurement accuracy, enforce regulatory compliance (ISO/IEC 17025, FDA 21 CFR Part 11, IATF 16949), and proactively eliminate overdue instrument usage across manufacturing lines.

### Core Architectural Principles:
1. **Separation of Concerns**: Strict decoupling of Storage, Domain Business Logic, Application Services, Data Generation, Presentation, and Validation.
2. **Deterministic Reproducibility**: All random master and transaction generators utilize explicit random seeds (`20261022`) guaranteeing bit-for-bit reproducible baseline records.
3. **Immutability & Audit Trail**: Operational records, calibrations, and certificates are append-only. State changes are captured as explicit audit records with JSON snapshots of old and new states.
4. **Zero-Data-Leakage Validation**: The anomaly detection engine operates strictly on raw database relations using pure business heuristics. Isolated ground truth (`data/ground_truth/ground_truth.csv`) is preserved solely for post-hoc precision/recall evaluation.
5. **Portability**: Schema adheres to ANSI SQL-92 standards and SQLAlchemy 2.0 ORM, enabling seamless switching between local SQLite (with enforced `PRAGMA foreign_keys = ON`) and enterprise PostgreSQL.

---

## 2. Layered Architecture Diagram

```mermaid
graph TD
    subgraph UI_Layer [Presentation Layer - Streamlit & Plotly]
        UI_Dash[Executive Dashboard]
        UI_Inst[Instrument Registry]
        UI_Cal[Calibration & Certs]
        UI_Gate[Shopfloor Gatekeeper Simulator]
        UI_WO[Work Orders & CAPA]
        UI_Audit[Audit Trail Ledger]
        UI_DQ[Data Quality & Benchmarks]
    end

    subgraph Service_Layer [Application Services]
        S_Inst[InstrumentService]
        S_Cal[CalibrationService]
        S_Prod[ProductionService]
        S_Audit[AuditService]
    end

    subgraph Business_Logic [Domain Business Logic Layer]
        BL_Sched[Calibration Scheduling & Intervals]
        BL_Math[Deviation & Tolerance PASS/FAIL]
        BL_Cert[Certificate Reconciliation Engine]
        BL_Gate[8-Point Production Gatekeeper]
        BL_CAPA[Failure Containment & Lot Tracing]
        BL_Alert[Compliance Alert Engine]
    end

    subgraph Quality_Layer [Verification & Validation Harness]
        V_Integ[Relational Integrity Verifier]
        V_Life[Lifecycle State Transitions]
        V_Eval[Evaluation Metrics & Anomaly Detector]
        V_Repro[Dual-Run Reproducibility Verifier]
        GT[Isolated Ground Truth Registry]
    end

    subgraph Data_Layer [Relational Storage & Filesystem]
        DB[(SQLAlchemy / SQLite / PostgreSQL)]
        CSV_EXP[data/exports/*.csv]
        JSON_EXP[data/exports/*.json]
        SQL_SCHEMA[database/schema.sql]
    end

    UI_Layer --> Service_Layer
    Service_Layer --> Business_Logic
    Business_Logic --> Data_Layer
    Service_Layer --> Data_Layer
    Quality_Layer --> Business_Logic
    Quality_Layer --> Data_Layer
    Quality_Layer -.-> GT
```

---

## 3. Entity Relational Architecture (Core & Supporting Entities)

```mermaid
erDiagram
    SUPPLIER ||--o{ ASSET : supplies
    INSTRUMENT_TYPE ||--o{ ASSET : classifies
    INSTRUMENT_TYPE ||--o{ CALIBRATION_PLAN : defines
    CALIBRATION_PLAN ||--o{ ASSET : prescribes
    CALIBRATION_PLAN ||--o{ CALIBRATION_EVENT : governs
    ASSET ||--o{ CALIBRATION_EVENT : undergoes
    CALIBRATION_EVENT ||--o{ CERTIFICATE : issues
    ASSET ||--o{ CERTIFICATE : references
    ASSET ||--o{ WORK_ORDER : requires
    ASSET ||--o{ PRODUCTION_USE : engaged_in
    ASSET ||--o{ ALERT : triggers
    ASSET ||--o{ CALIBRATION_EXTENSION : granted
    CALIBRATION_EVENT ||--o{ CORRECTIVE_ACTION : initiates
    CALIBRATION_EVENT ||--o{ IMPACT_ASSESSMENT : triggers
    WORK_ORDER ||--o{ CORRECTIVE_ACTION : remediates
```

---

## 4. Multi-Tier Module Breakdown

### 4.1 Storage & Relational Layer (`database/`)
- `connection.py`: Manages thread-safe session factories, connection pools, and SQLite WAL pragmas with foreign key cascade/restrict guarantees.
- `models.py`: Declarative ORM models for all 10 required core entities (`Supplier`, `InstrumentType`, `CalibrationPlan`, `Asset`, `CalibrationEvent`, `Certificate`, `WorkOrder`, `ProductionUse`, `Alert`, `AuditRecord`) and 4 supporting entities (`CorrectiveAction`, `ImpactAssessment`, `CalibrationExtension`, `WorkOrderAsset`).
- `schema.sql`: ANSI-compliant DDL with explicit primary keys, foreign keys, unique constraints, and optimized B-tree indexes.

### 4.2 Domain Business Logic Layer (`business_logic/`)
- `calibration.py`: Deterministic calculation of absolute deviation `|measured - reference|` and tolerance check `deviation <= tolerance ? PASS : FAIL`. Calculates next scheduled due dates.
- `scheduling.py`: Real-time calendar interval additions, overdue status checking, and emergency extension reconciliations.
- `production_validation.py`: The Shopfloor Gatekeeper. Enforces the 8 mandatory compliance checks before instrument usage is allowed.
- `certificates.py`: Cross-reconciliation between certificates, calibration events, and assets. Identifies mismatches, missing certs, and expired credentials.
- `corrective_actions.py`: Retrospective production batch tracing (identifies all lots produced between last known valid calibration and failure timestamp).
- `work_orders.py`: Maintenance order lifecycle dispatching and Mean Time to Repair (MTTR) analytics.
- `alerts.py`: Standardized alert generation across 8 compliance hazards.

### 4.3 Application Services Layer (`services/`)
- Clean interface between the presentation layer and database, encapsulating transactions, validation, and audit recording.

### 4.4 Presentation Layer (`dashboard/`)
- High-performance Streamlit 1.57 dashboard with Plotly 6.9 interactive visualizations, real-time KPI scorecards, multi-criteria filtering, and live gatekeeper simulator.

### 4.5 Data Quality & Validation Layer (`validation/`)
- Independent verification suite executing relational integrity checks, state transition audits, bit-for-bit reproducibility comparisons, and zero-leakage anomaly detection benchmarks.