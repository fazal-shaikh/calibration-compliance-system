# Data Flow Specification: Enterprise Calibration & Compliance System

## 1. Primary Data Flows & Lifecycle Sequences

### Data Flow 1: Empirical Calibration Test Execution & Certificate Issuance

```mermaid
sequenceDiagram
    autonumber
    actor Tech as Metrology Technician
    participant CS as CalibrationService
    participant BL as BusinessLogic Engine
    participant DB as Relational Database
    participant AS as AuditService

    Tech->>CS: Submit Test (asset_id, measured_val, ref_val)
    CS->>BL: calculate_deviation(measured, ref)
    BL-->>CS: deviation
    CS->>BL: evaluate_result(deviation, plan_tolerance)
    BL-->>CS: result (PASS / FAIL)

    alt Result == PASS
        CS->>BL: calculate_next_due_date(cal_date, plan.interval)
        BL-->>CS: next_due_date
        CS->>DB: INSERT CalibrationEvent
        CS->>DB: UPDATE Asset (last_cal=date, next_due=next_due, status=ACTIVE)
        CS->>DB: INSERT Certificate (status=VALID, SHA-256 hash)
        CS->>AS: log_audit_event("calibration_events", cal_id, "INSERT")
        CS-->>Tech: Test Passed & Certificate Issued
    else Result == FAIL
        CS->>DB: INSERT CalibrationEvent (result=FAIL)
        CS->>DB: UPDATE Asset (status=QUARANTINED)
        CS->>BL: create_failure_containment(...)
        BL-->>CS: ImpactAssessment & CAPA package
        CS->>DB: INSERT ImpactAssessment (OPEN)
        CS->>DB: INSERT CorrectiveAction (OPEN)
        CS->>DB: INSERT WorkOrder (CRITICAL, FAILED_CALIBRATION)
        CS->>DB: INSERT Alert (CRITICAL, FAILED_CALIBRATION)
        CS->>AS: log_audit_event("calibration_events", cal_id, "FAIL_QUARANTINE")
        CS-->>Tech: Test Failed, Instrument Quarantined & CAPA Initiated
    end
```

---

### Data Flow 2: Real-Time Shopfloor Usage Gatekeeper Validation

```mermaid
sequenceDiagram
    autonumber
    actor Op as Plant Operator
    participant PS as ProductionService
    participant Gate as Gatekeeper Engine (8 Gates)
    participant DB as Relational Database
    participant Alt as Alert Engine

    Op->>PS: Request Instrument Usage (asset_id, batch_id, line_id)
    PS->>DB: Fetch Asset, Latest Calibration, Certificate, Active WOs, Extensions
    DB-->>PS: Records
    PS->>Gate: evaluate_production_usage(...)
    Gate-->>PS: Decision (ALLOWED / BLOCKED / ALLOWED_WITH_EXCEPTION)

    PS->>DB: INSERT ProductionUse (usage_id, decision, policy_code, reason)
    
    alt Decision == BLOCKED
        PS->>Alt: Trigger Alert (UNAUTHORIZED_USAGE, CRITICAL)
        Alt->>DB: INSERT Alert
        PS-->>Op: 🛑 Usage Prohibited (Action Blocked)
    else Decision == ALLOWED_WITH_EXCEPTION
        PS-->>Op: ⚠️ Usage Allowed under Emergency Extension
    else Decision == ALLOWED
        PS-->>Op: ✅ Usage Authorized (Gate Passed)
    end
```

---

### Data Flow 3: Post-Failure Retrospective Lot Tracing Flow

```mermaid
sequenceDiagram
    autonumber
    participant Engine as Containment Engine
    participant DB as Relational Database
    participant IA as ImpactAssessment Model
    participant QA as Quality Manager

    Engine->>DB: Query last known valid (passed) calibration timestamp
    DB-->>Engine: timestamp_valid
    Engine->>DB: SELECT * FROM production_uses WHERE asset_id=X AND usage_timestamp BETWEEN timestamp_valid AND failure_date
    DB-->>Engine: Affected Uses List
    Engine->>Engine: Group affected uses by batch_id
    Engine->>DB: INSERT ImpactAssessment (affected_batches_count, affected_uses_count, risk_level)
    QA->>DB: Inspect ImpactAssessment in Dashboard
    QA->>DB: Disposition Batches ("Quarantined Pending Batch Review")
```

---

### Data Flow 4: Zero-Data-Leakage Anomaly Detection Pipeline

```mermaid
graph LR
    subgraph Raw_Data [Relational Database]
        Assets[(assets)]
        Cal[(calibration_events)]
        Certs[(certificates)]
        Uses[(production_uses)]
    end

    subgraph Independent_Detector [Anomaly Detection Engine]
        R1[Scan Due Date Interval Mismatches]
        R2[Scan Expired Instrument Bypasses]
        R3[Scan Certificate Asset Mismatches]
        R4[Scan Orphaned Failed Calibrations]
    end

    subgraph Benchmark [Evaluation Harness]
        GT[(Isolated ground_truth.csv)]
        Comp{Benchmark Comparator}
        Metrics[Precision, Recall, F1-Score]
    end

    Raw_Data --> Independent_Detector
    Independent_Detector --> Comp
    GT --> Comp
    Comp --> Metrics
```