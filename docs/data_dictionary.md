# Data Dictionary: Enterprise Calibration Management & Compliance System

This data dictionary formally documents the relational schema, entity attributes, integrity constraints, permitted domains, and validation rules across all 10 core entities and 4 supporting entities.

---

## 1. Core Entity: `suppliers`
Maintains verified vendor master data for original equipment manufacturers (OEMs) and certified external calibration laboratories.

| Field Name | Description | Data Type | Req/Opt | Allowed Values | Units | Uniqueness | Validation Rule | PK/FK |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `supplier_id` | Unique alphanumeric supplier identifier | VARCHAR(32) | Required | Format: `SUP-XXX` | N/A | Unique | Non-empty alphanumeric | Primary Key |
| `name` | Legal business name of the vendor/lab | VARCHAR(255) | Required | Any valid string | N/A | Non-unique | Length >= 2 chars | None |
| `contact_email`| Official technical or commercial contact | VARCHAR(255) | Optional | Valid email format | N/A | Non-unique | Regex: `^[\w\.-]+@[\w\.-]+\.\w+$` | None |
| `phone` | Primary vendor telephone contact | VARCHAR(64) | Optional | Standard phone chars | N/A | Non-unique | Chars in `+0-9() -` | None |
| `address` | Registered business or laboratory address | VARCHAR(500) | Optional | Valid address string | N/A | Non-unique | Length <= 500 chars | None |
| `is_accredited`| ISO/IEC 17025 accreditation status | BOOLEAN | Required | `true`, `false` | N/A | Non-unique | Boolean | None |
| `accreditation_number` | Formal accreditation body certificate ID | VARCHAR(128) | Optional | String | N/A | Non-unique | Required if `is_accredited` is true | None |
| `created_at` | Record creation timestamp | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | Must not be future timestamp | None |

---

## 2. Core Entity: `instrument_types`
Catalog of instrument models, measurement classes, measurement units, and baseline factory tolerances.

| Field Name | Description | Data Type | Req/Opt | Allowed Values | Units | Uniqueness | Validation Rule | PK/FK |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `type_id` | Unique identifier for instrument class | VARCHAR(32) | Required | Format: `TYP-XXX` | N/A | Unique | Alphanumeric code | Primary Key |
| `category` | Physical measurement domain | VARCHAR(64) | Required | `Pressure`, `Temperature`, `Flow`, `Electrical`, `Dimensional`, `Weighing` | N/A | Non-unique | Must belong to defined enum | None |
| `model_name` | Commercial model designation | VARCHAR(255) | Required | Alphanumeric string | N/A | Non-unique | Non-empty | None |
| `manufacturer`| OEM brand name | VARCHAR(255) | Required | String | N/A | Non-unique | Non-empty | None |
| `measurement_range`| Calibrated operating span | VARCHAR(128) | Required | e.g., "0-100 bar", "-50 to 200 C" | Varies | Non-unique | Must define span format | None |
| `default_interval_days` | Standard calibration recurrence | INTEGER | Required | 30 to 730 | Days | Non-unique | Must be > 0 | None |
| `default_tolerance` | Allowable error threshold | FLOAT | Required | Float > 0.0 | Category Unit | Non-unique | Must be strictly positive | None |
| `unit_of_measure` | Physical engineering unit | VARCHAR(32) | Required | `bar`, `deg C`, `L/min`, `V`, `mm`, `kg` | N/A | Non-unique | Standard ISO engineering unit | None |
| `created_at` | Record creation timestamp | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | Must not be future timestamp | None |

---

## 3. Core Entity: `calibration_plans`
Defines prescriptive calibration procedures, recurrence schedules, and strict tolerance criteria for instruments.

| Field Name | Description | Data Type | Req/Opt | Allowed Values | Units | Uniqueness | Validation Rule | PK/FK |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `plan_id` | Unique identifier for calibration plan | VARCHAR(32) | Required | Format: `PLAN-XXX` | N/A | Unique | Alphanumeric code | Primary Key |
| `type_id` | Reference to parent instrument type | VARCHAR(32) | Required | Existing `type_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`instrument_types.type_id`) |
| `name` | Descriptive protocol title | VARCHAR(255) | Required | String | N/A | Non-unique | Non-empty | None |
| `interval_days`| Frequency interval between calibrations | INTEGER | Required | 30, 60, 90, 180, 365, 730 | Days | Non-unique | Interval > 0 | None |
| `tolerance` | Maximum allowable measurement deviation | FLOAT | Required | Float > 0.0 | Eng Unit | Non-unique | Must be positive | None |
| `mandatory_certificate` | Flag requiring certified verification | BOOLEAN | Required | `true`, `false` | N/A | Non-unique | Boolean | None |
| `standard_operating_procedure` | SOP documentation reference | VARCHAR(500) | Optional | Path or SOP code | N/A | Non-unique | Valid SOP code | None |
| `created_at` | Record creation timestamp | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | Timestamp <= current | None |

---

## 4. Core Entity: `assets`
Individual physical measurement instruments installed across factory production lines.

| Field Name | Description | Data Type | Req/Opt | Allowed Values | Units | Uniqueness | Validation Rule | PK/FK |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `asset_id` | Deterministic asset tag | VARCHAR(32) | Required | Format: `AST-XXXXXX` | N/A | Unique | Regex: `^AST-\d{6}$` | Primary Key |
| `serial_number`| Manufacturer factory serial number | VARCHAR(128) | Required | Unique alphanumeric string | N/A | Unique | Non-empty, unique across assets | None |
| `name` | Human-readable asset description | VARCHAR(255) | Required | String | N/A | Non-unique | Non-empty | None |
| `type_id` | Instrument type reference | VARCHAR(32) | Required | Existing `type_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`instrument_types.type_id`) |
| `plan_id` | Assigned calibration plan | VARCHAR(32) | Required | Existing `plan_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`calibration_plans.plan_id`) |
| `supplier_id`| Supplier / lab reference | VARCHAR(32) | Required | Existing `supplier_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`suppliers.supplier_id`) |
| `department` | Manufacturing department | VARCHAR(128) | Required | QA, Machining, Assembly, Thermal, Packaging, Lab | N/A | Non-unique | Valid department list | None |
| `location` | Specific line or workstation tag | VARCHAR(128) | Required | e.g., Line-A1, Cell-04 | N/A | Non-unique | Non-empty | None |
| `status` | Current operational state | VARCHAR(32) | Required | `ACTIVE`, `IN_CALIBRATION`, `OUT_OF_SERVICE`, `RETIRED`, `QUARANTINED` | N/A | Non-unique | Valid lifecycle state | None |
| `commissioning_date` | Initial deployment timestamp | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | Must be <= current date | None |
| `last_calibration_date` | Timestamp of latest calibration | TIMESTAMP | Optional | ISO-8601 UTC timestamp | Time | Non-unique | Must be >= commissioning_date | None |
| `next_due_date` | Scheduled calibration deadline | TIMESTAMP | Optional | ISO-8601 UTC timestamp | Time | Non-unique | Derived from last_calibration + interval | None |
| `created_at` | Record creation timestamp | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | None | None |
| `updated_at` | Record update timestamp | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | Updated on modification | None |

---

## 5. Core Entity: `calibration_events`
Individual calibration tests performed by certified metrology technicians.

| Field Name | Description | Data Type | Req/Opt | Allowed Values | Units | Uniqueness | Validation Rule | PK/FK |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `calibration_id` | Deterministic calibration event ID | VARCHAR(64) | Required | Format: `CAL-<asset_id>-<year>-<seq>` | N/A | Unique | Regex formatted | Primary Key |
| `asset_id` | Target calibrated asset | VARCHAR(32) | Required | Existing `asset_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`assets.asset_id`) |
| `plan_id` | Applied calibration procedure plan | VARCHAR(32) | Required | Existing `plan_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`calibration_plans.plan_id`) |
| `calibration_date` | Timestamp when test was executed | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | Must be >= asset commissioning | None |
| `technician` | Certified metrologist ID or name | VARCHAR(128) | Required | Non-empty string | N/A | Non-unique | Non-empty | None |
| `measured_value` | Actual sensor observation | FLOAT | Required | Any real number | Eng Unit | Non-unique | None | None |
| `reference_value` | Standard master artifact value | FLOAT | Required | Any real number | Eng Unit | Non-unique | Reference must be non-zero | None |
| `tolerance` | Maximum allowable tolerance limit | FLOAT | Required | Float > 0.0 | Eng Unit | Non-unique | Must match plan tolerance | None |
| `deviation` | Absolute measurement discrepancy | FLOAT | Required | Float >= 0.0 | Eng Unit | Non-unique | `= abs(measured_value - reference_value)` | None |
| `result` | Formal evaluation outcome | VARCHAR(16) | Required | `PASS`, `FAIL` | N/A | Non-unique | `deviation <= tolerance ? PASS : FAIL` | None |
| `temperature_celsius` | Ambient laboratory temperature | FLOAT | Optional | 18.0 to 26.0 | °C | Non-unique | Environmental envelope | None |
| `humidity_percent` | Ambient relative humidity | FLOAT | Optional | 30.0 to 70.0 | % RH | Non-unique | Environmental envelope | None |
| `notes` | Metrologist observations | TEXT | Optional | Free text | N/A | Non-unique | None | None |
| `created_at` | Record creation timestamp | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | None | None |

---

## 6. Core Entity: `certificates`
Official metrology compliance certificates attesting to calibration integrity and traceability.

| Field Name | Description | Data Type | Req/Opt | Allowed Values | Units | Uniqueness | Validation Rule | PK/FK |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `certificate_id` | Deterministic certificate identifier | VARCHAR(64) | Required | Format: `CERT-<calibration_id>` | N/A | Unique | Format strictly matched | Primary Key |
| `certificate_number` | Formal regulatory certificate serial | VARCHAR(128) | Required | Alphanumeric serial | N/A | Unique | Must be globally unique | None |
| `calibration_id` | Linked calibration event | VARCHAR(64) | Required | Existing `calibration_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`calibration_events.calibration_id`) |
| `asset_id` | Referenced physical instrument | VARCHAR(32) | Required | Existing `asset_id` | N/A | Non-unique | Must match calibration event asset_id | Foreign Key (`assets.asset_id`) |
| `issue_date` | Timestamp certificate was signed | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | Must be >= calibration_date | None |
| `expiry_date` | Regulatory validity cutoff | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | Must be > issue_date | None |
| `verification_status` | Current certificate validity state | VARCHAR(32) | Required | `VALID`, `EXPIRED`, `REVOKED`, `MISMATCHED` | N/A | Non-unique | Enum check | None |
| `issuer_name` | Accompanying laboratory or authority | VARCHAR(255) | Required | Non-empty string | N/A | Non-unique | Non-empty | None |
| `digital_signature_hash` | SHA-256 integrity digest | VARCHAR(128) | Optional | 64-char hex string | N/A | Non-unique | Cryptographic hash | None |
| `file_path` | Storage URI for PDF certificate | VARCHAR(500) | Optional | Valid file URI | N/A | Non-unique | Valid path | None |
| `created_at` | Record creation timestamp | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | None | None |

---

## 7. Core Entity: `work_orders`
Scheduled or emergency maintenance interventions, preventive calibrations, and failure investigations.

| Field Name | Description | Data Type | Req/Opt | Allowed Values | Units | Uniqueness | Validation Rule | PK/FK |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `work_order_id` | Deterministic work order reference | VARCHAR(64) | Required | Format: `WO-<year>-<seq>` | N/A | Unique | Format enforced | Primary Key |
| `asset_id` | Physical instrument requiring service | VARCHAR(32) | Required | Existing `asset_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`assets.asset_id`) |
| `order_type` | Nature of maintenance action | VARCHAR(64) | Required | `UPCOMING_CALIBRATION`, `OVERDUE_CALIBRATION`, `FAILED_CALIBRATION`, `CORRECTIVE_MAINTENANCE`, `INVESTIGATION` | N/A | Non-unique | Enum check | None |
| `priority` | Operational dispatch urgency | VARCHAR(16) | Required | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | N/A | Non-unique | Enum check | None |
| `status` | Work execution stage | VARCHAR(32) | Required | `OPEN`, `IN_PROGRESS`, `PENDING_REVIEW`, `COMPLETED`, `CANCELLED` | N/A | Non-unique | Valid workflow state | None |
| `assigned_technician` | Lead maintenance engineer | VARCHAR(128) | Optional | Personnel name/ID | N/A | Non-unique | None | None |
| `creation_date` | Timestamp order was opened | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | Creation <= completion | None |
| `scheduled_date` | Target execution deadline | TIMESTAMP | Optional | ISO-8601 UTC timestamp | Time | Non-unique | None | None |
| `completion_date` | Timestamp order was fulfilled | TIMESTAMP | Optional | ISO-8601 UTC timestamp | Time | Non-unique | Must be >= creation_date | None |
| `downtime_hours` | Total hours asset was unavailable | FLOAT | Required | Float >= 0.0 | Hours | Non-unique | Must be non-negative | None |
| `cost` | Financial expenditure incurred | FLOAT | Required | Float >= 0.0 | Currency | Non-unique | Must be non-negative | None |
| `resolution_notes` | Post-maintenance closure log | TEXT | Optional | Free text | N/A | Non-unique | None | None |
| `created_at` | Record creation timestamp | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | None | None |
| `updated_at` | Record update timestamp | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | None | None |

---

## 8. Core Entity: `production_uses`
Real-time shopfloor transactions capturing every attempt by operators to employ an instrument in production.

| Field Name | Description | Data Type | Req/Opt | Allowed Values | Units | Uniqueness | Validation Rule | PK/FK |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `usage_id` | Deterministic transaction ID | VARCHAR(128) | Required | Format: `USE-<asset_id>-<timestamp>` | N/A | Unique | Format enforced | Primary Key |
| `asset_id` | Target instrument used | VARCHAR(32) | Required | Existing `asset_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`assets.asset_id`) |
| `usage_timestamp` | Exact time instrument was engaged | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | Must be valid datetime | None |
| `batch_id` | Manufactured lot or batch identifier | VARCHAR(128) | Required | e.g. `BATCH-2026-00123` | N/A | Non-unique | Non-empty | None |
| `production_line` | Factory line where use occurred | VARCHAR(64) | Required | e.g. `Line-01` to `Line-10` | N/A | Non-unique | Non-empty | None |
| `operator_id` | Plant operator badge identifier | VARCHAR(64) | Required | e.g. `OP-1042` | N/A | Non-unique | Non-empty | None |
| `decision` | Automated Gatekeeper verdict | VARCHAR(32) | Required | `ALLOWED`, `BLOCKED`, `ALLOWED_WITH_EXCEPTION` | N/A | Non-unique | Enum check | None |
| `policy_applied` | Standard rule code applied | VARCHAR(64) | Required | e.g. `POL-CAL-001`, `POL-OVERDUE-002`, `POL-EXT-003` | N/A | Non-unique | Non-empty code | None |
| `reason` | Technical justification for decision | TEXT | Required | Human and audit-readable rationale | N/A | Non-unique | Detailed explanation | None |
| `validation_passed` | Boolean status indicating pass/fail | BOOLEAN | Required | `true`, `false` | N/A | Non-unique | Boolean | None |
| `created_at` | Record creation timestamp | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | None | None |

---

## 9. Core Entity: `alerts`
Real-time compliance alerts triggered on overdue calibrations, expired certificates, or unauthorized usage attempts.

| Field Name | Description | Data Type | Req/Opt | Allowed Values | Units | Uniqueness | Validation Rule | PK/FK |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `alert_id` | Deterministic alert identifier | VARCHAR(64) | Required | Format: `ALT-XXXXXX` | N/A | Unique | Alphanumeric | Primary Key |
| `asset_id` | Associated asset reference | VARCHAR(32) | Optional | Existing `asset_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`assets.asset_id`) |
| `alert_type` | Categorization of compliance hazard | VARCHAR(64) | Required | `UPCOMING_CALIBRATION`, `OVERDUE_CALIBRATION`, `FAILED_CALIBRATION`, `MISSING_CERTIFICATE`, `EXPIRED_CERTIFICATE`, `UNAUTHORIZED_USAGE`, `MISSING_IMPACT_ASSESSMENT`, `EXTENSION_EXPIRY` | N/A | Non-unique | Enum check | None |
| `severity` | Threat level to quality/safety | VARCHAR(16) | Required | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | N/A | Non-unique | Enum check | None |
| `message` | Clear actionable warning message | TEXT | Required | Non-empty description | N/A | Non-unique | Non-empty | None |
| `status` | Alert lifecycle status | VARCHAR(32) | Required | `ACTIVE`, `ACKNOWLEDGED`, `RESOLVED`, `DISMISSED` | N/A | Non-unique | Enum check | None |
| `created_at` | Generation timestamp | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | <= acknowledged_at | None |
| `acknowledged_at` | Timestamp operator acknowledged | TIMESTAMP | Optional | ISO-8601 UTC timestamp | Time | Non-unique | >= created_at | None |
| `resolved_at` | Timestamp issue was cleared | TIMESTAMP | Optional | ISO-8601 UTC timestamp | Time | Non-unique | >= created_at | None |

---

## 10. Core Entity: `audit_records`
Immutable append-only ledger tracking all mutations, status transitions, and administrative overrides.

| Field Name | Description | Data Type | Req/Opt | Allowed Values | Units | Uniqueness | Validation Rule | PK/FK |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `audit_id` | Sequential immutable audit ID | VARCHAR(64) | Required | Format: `AUD-XXXXXX` | N/A | Unique | Monotonic string | Primary Key |
| `table_name` | Name of modified database entity | VARCHAR(64) | Required | Valid table name | N/A | Non-unique | Must exist in schema | None |
| `record_id` | Primary key of affected record | VARCHAR(128) | Required | String identifier | N/A | Non-unique | Non-empty | None |
| `action` | Type of mutation performed | VARCHAR(16) | Required | `INSERT`, `UPDATE`, `DELETE` | N/A | Non-unique | Enum check | None |
| `actor` | System account or operator ID | VARCHAR(128) | Required | Non-empty user string | N/A | Non-unique | Non-empty | None |
| `timestamp` | Time of mutation occurrence | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | Monotonic progression | None |
| `old_values_json` | Pre-mutation state JSON snapshot | TEXT | Optional | Valid JSON format or NULL | N/A | Non-unique | Valid JSON parser | None |
| `new_values_json` | Post-mutation state JSON snapshot | TEXT | Optional | Valid JSON format or NULL | N/A | Non-unique | Valid JSON parser | None |
| `reason` | Engineering rationale for change | VARCHAR(500) | Optional | Description string | N/A | Non-unique | None | None |

---

## 11. Supporting Entity: `corrective_actions` (CAPA)
Formal Corrective and Preventive Action records initiated following failed calibration outcomes.

| Field Name | Description | Data Type | Req/Opt | Allowed Values | Units | Uniqueness | Validation Rule | PK/FK |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `corrective_action_id` | CAPA tracking number | VARCHAR(64) | Required | Format: `CAPA-<year>-<seq>` | N/A | Unique | Format enforced | Primary Key |
| `calibration_id` | Initiating failed calibration event | VARCHAR(64) | Required | Existing `calibration_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`calibration_events.calibration_id`) |
| `asset_id` | Out-of-spec physical instrument | VARCHAR(32) | Required | Existing `asset_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`assets.asset_id`) |
| `work_order_id` | Associated remediation work order | VARCHAR(64) | Optional | Existing `work_order_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`work_orders.work_order_id`) |
| `status` | CAPA progression stage | VARCHAR(32) | Required | `OPEN`, `IN_PROGRESS`, `VERIFIED`, `CLOSED` | N/A | Non-unique | Enum check | None |
| `root_cause` | Metrological failure diagnosis | TEXT | Optional | Free text explanation | N/A | Non-unique | None | None |
| `containment_action`| Immediate quarantine or stop-use | TEXT | Optional | Free text explanation | N/A | Non-unique | None | None |
| `preventive_action` | Long-term procedural modification | TEXT | Optional | Free text explanation | N/A | Non-unique | None | None |
| `assigned_to` | Lead Quality / Metrology Engineer | VARCHAR(128) | Optional | User identifier | N/A | Non-unique | None | None |
| `target_date` | Required remediation deadline | TIMESTAMP | Optional | ISO-8601 UTC timestamp | Time | Non-unique | >= created_at | None |
| `closed_date` | Formal sign-off closure timestamp | TIMESTAMP | Optional | ISO-8601 UTC timestamp | Time | Non-unique | >= created_at | None |
| `created_at` | Record creation timestamp | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | None | None |

---

## 12. Supporting Entity: `impact_assessments`
Systematic retrospective analysis of all production batches manufactured between the last known valid calibration and failure date.

| Field Name | Description | Data Type | Req/Opt | Allowed Values | Units | Uniqueness | Validation Rule | PK/FK |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `assessment_id` | Impact assessment reference | VARCHAR(64) | Required | Format: `IMP-<year>-<seq>` | N/A | Unique | Format enforced | Primary Key |
| `calibration_id` | Triggering failed calibration event | VARCHAR(64) | Required | Existing `calibration_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`calibration_events.calibration_id`) |
| `asset_id` | Target instrument | VARCHAR(32) | Required | Existing `asset_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`assets.asset_id`) |
| `investigation_status` | Status of containment inquiry | VARCHAR(32) | Required | `OPEN`, `IN_INVESTIGATION`, `CONCLUDED`, `DISPOSITIONED` | N/A | Non-unique | Enum check | None |
| `risk_level` | Assessed safety/quality hazard | VARCHAR(16) | Required | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | N/A | Non-unique | Enum check | None |
| `affected_batches_count` | Number of compromised production lots | INTEGER | Required | Integer >= 0 | Lots | Non-unique | Must be non-negative | None |
| `affected_usage_events_count` | Number of linked shopfloor uses | INTEGER | Required | Integer >= 0 | Events | Non-unique | Must be non-negative | None |
| `investigation_summary` | Summary of batch impact findings | TEXT | Optional | Free text narrative | N/A | Non-unique | None | None |
| `disposition` | Final product disposition | VARCHAR(255) | Optional | Quarantine, Retest, Scrapped, Released with Concession | N/A | Non-unique | None | None |
| `assessor` | Quality Assurance Manager | VARCHAR(128) | Optional | User identifier | N/A | Non-unique | None | None |
| `assessment_date` | Initial inquiry opening date | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | None | None |
| `closed_date` | Investigation sign-off date | TIMESTAMP | Optional | ISO-8601 UTC timestamp | Time | Non-unique | >= assessment_date | None |
| `created_at` | Record creation timestamp | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | None | None |

---

## 13. Supporting Entity: `calibration_extensions`
Formal, risk-evaluated emergency extensions temporarily extending instrument validity under regulated exceptions.

| Field Name | Description | Data Type | Req/Opt | Allowed Values | Units | Uniqueness | Validation Rule | PK/FK |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `extension_id` | Extension permit reference | VARCHAR(64) | Required | Format: `EXT-<year>-<seq>` | N/A | Unique | Format enforced | Primary Key |
| `asset_id` | Target instrument | VARCHAR(32) | Required | Existing `asset_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`assets.asset_id`) |
| `original_due_date`| Scheduled baseline deadline | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | None | None |
| `extended_due_date`| New granted expiration date | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | Extended > Original (max 30 days) | None |
| `approved_by` | Authorizing Quality Director | VARCHAR(128) | Required | Authorized personnel ID | N/A | Non-unique | Non-empty | None |
| `approval_date` | Date of executive sign-off | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | <= extended_due_date | None |
| `justification` | Documented business/engineering rationale | TEXT | Required | Non-empty narrative | N/A | Non-unique | Min length >= 10 chars | None |
| `status` | Extension validity status | VARCHAR(32) | Required | `ACTIVE`, `EXPIRED`, `SUPERSEDED`, `REVOKED` | N/A | Non-unique | Enum check | None |
| `created_at` | Record creation timestamp | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | None | None |

---

## 14. Supporting Bridge Entity: `work_order_assets`
Many-to-many bridge linking multiple assets (such as reference standards and secondary targets) to work orders.

| Field Name | Description | Data Type | Req/Opt | Allowed Values | Units | Uniqueness | Validation Rule | PK/FK |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | Surrogate bridge link ID | VARCHAR(64) | Required | Format: `WOA-<seq>` | N/A | Unique | Non-empty | Primary Key |
| `work_order_id` | Target work order | VARCHAR(64) | Required | Existing `work_order_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`work_orders.work_order_id`) |
| `asset_id` | Referenced instrument | VARCHAR(32) | Required | Existing `asset_id` | N/A | Non-unique | Foreign Key check | Foreign Key (`assets.asset_id`) |
| `role` | Functional role in maintenance | VARCHAR(64) | Required | `PRIMARY`, `REFERENCE_STANDARD`, `VERIFICATION_TARGET` | N/A | Non-unique | Enum check | None |
| `created_at` | Link creation timestamp | TIMESTAMP | Required | ISO-8601 UTC timestamp | Time | Non-unique | None | None |