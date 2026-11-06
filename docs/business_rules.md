# Business Rules Specification: Enterprise Calibration & Compliance System

This document outlines the prescriptive operational policies, metrological criteria, and automated enforcement mechanisms implemented in the system.

---

## 1. Calibration Scheduling Rules

### Rule BR-SCHED-001: Due Date Determination
- The next calibration due date is deterministically calculated from the latest valid (passed) calibration event:
  $$\text{next\_due\_date} = \text{calibration\_date} + \text{interval\_days}$$
- Calibration intervals are dictated by the assigned `CalibrationPlan` (e.g., 90, 180, 365, or 730 days) based on instrument category and critical risk classification.

### Rule BR-SCHED-002: Overdue Status Classification
- An instrument is strictly classified as **OVERDUE** if:
  $$\text{as\_of\_date} > \text{next\_due\_date}$$
- There is **zero grace period** for overdue instruments unless covered by an authorized emergency extension.
- Overdue instruments automatically trigger HIGH severity alerts and proactive maintenance work orders.

### Rule BR-SCHED-003: Proactive Upcoming Notice
- An instrument enters the **UPCOMING** calibration window when:
  $$\text{as\_of\_date} \le \text{next\_due\_date} \le (\text{as\_of\_date} + 30\text{ days})$$
- Proactive work orders of type `UPCOMING_CALIBRATION` are dispatched with MEDIUM priority.

---

## 2. Empirical Calibration & Tolerance Rules

### Rule BR-CAL-001: Absolute Deviation Formula
- Metrologists observe sensor readings against calibrated reference standards. The absolute measurement deviation is calculated as:
  $$\text{deviation} = |\text{measured\_value} - \text{reference\_value}|$$
- The deviation must be rounded to 6 decimal places to prevent floating-point precision anomalies.

### Rule BR-CAL-002: Deterministic PASS/FAIL Evaluation
- The evaluation outcome is formulaically determined:
  $$\text{result} = \begin{cases} \text{PASS}, & \text{if } \text{deviation} \le \text{tolerance} \\ \text{FAIL}, & \text{if } \text{deviation} > \text{tolerance} \end{cases}$$
- System policies strictly prohibit manual override or independent assignment of the PASS/FAIL label.

---

## 3. Certificate Management Rules

### Rule BR-CERT-001: Mandatory Issuance
- Every calibration test resulting in `PASS` under a certified plan requires an ISO/IEC 17025 accredited certificate.
- Certificates must record: unique certificate serial, calibration ID, asset tag, issue date, expiry date, issuer name, and SHA-256 digital signature digest.

### Rule BR-CERT-002: Relational Reconcile & Expiry
- A certificate is `VALID` only if:
  1. $\text{certificate.asset\_id} == \text{calibration\_event.asset\_id}$
  2. $\text{as\_of\_date} \le \text{certificate.expiry\_date}$
  3. $\text{certificate.verification\_status} == \text{"VALID"}$
- Any mismatch between certificate asset reference and calibration event asset reference immediately flags the certificate as `MISMATCHED`.

---

## 4. Production Usage Gatekeeper Rules (8 Compliance Gates)

Before permitting an operator to engage an instrument in a manufacturing run, the automated gatekeeper enforces the following 8 checks:

```
[Shopfloor Usage Request]
       │
       ▼
1. Does Instrument Exist in Master Registry? ───► NO ───► BLOCKED (POL-GATE-001)
       │ YES
       ▼
2. Is Status ACTIVE? (Not QUARANTINED/RETIRED) ─► NO ───► BLOCKED (POL-GATE-002)
       │ YES
       ▼
3. Does Calibration History Exist? ─────────────► NO ───► BLOCKED (POL-GATE-003)
       │ YES
       ▼
4. Did Latest Applicable Calibration PASS? ────► NO ───► BLOCKED (POL-GATE-004)
       │ YES
       ▼
5. Are there Blocking Maintenance Orders? ──────► YES ──► BLOCKED (POL-GATE-007)
       │ NO
       ▼
6. Is Usage Date within Due Date Window?
       ├─► YES ─────────────────────────────┐
       └─► NO (Past Due Date)               │
             │                              │
             ▼                              │
       Has Valid Emergency Extension?       │
             ├─► YES ──► ALLOWED_WITH_EXCEPTION (POL-GATE-008)
             └─► NO  ──► BLOCKED (POL-GATE-005)
                                            │
       ┌────────────────────────────────────┘
       ▼
7. Is Calibration Certificate Valid & Reconciled? ──► NO ──► BLOCKED (POL-GATE-006)
       │ YES
       ▼
8. ALL GATES PASSED ────────────────────────────► ALLOWED (POL-GATE-000)
```

---

## 5. Emergency Calibration Extension Rules

### Rule BR-EXT-001: Regulated Concession Policy
- Under exceptional circumstances (e.g. active high-priority batch production while waiting for standard laboratory turnaround), an emergency extension may be granted.
- **Constraints**:
  1. Maximum extension duration: strictly $\le 30$ days.
  2. Requires formal written justification and authorization from Quality Director.
  3. Original baseline due date is immutable and preserved for audit history.
  4. Instrument usage during this window is logged as `ALLOWED_WITH_EXCEPTION`.

---

## 6. Failure Containment, Quarantine, and Retrospective Impact Assessment

### Rule BR-FAIL-001: Automatic Quarantining
- Whenever an empirical calibration test results in `FAIL`:
  1. Asset status is immediately updated to `QUARANTINED`.
  2. Subsequent production gatekeeper checks return `BLOCKED`.
  3. A CRITICAL `WorkOrder` and CRITICAL `Alert` are automatically spawned.

### Rule BR-FAIL-002: Mandatory CAPA Initiation
- A formal Corrective and Preventive Action (CAPA) record is generated (`status = 'OPEN'`).
- A failed calibration is **never considered resolved** merely because a maintenance work order was generated; the CAPA must be investigated, root-caused, and formally dispositioned.

### Rule BR-FAIL-003: Retrospective Production Lot Tracing
- An `ImpactAssessment` is automatically triggered.
- The engine scans all `ProductionUse` transactions to identify every production batch processed on that instrument between the **last known valid calibration** and the **failure timestamp**.
- Compromised WIP batches are tagged for quality quarantine and re-testing.