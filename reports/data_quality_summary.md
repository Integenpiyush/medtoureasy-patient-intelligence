# Data Quality & Reconciliation Audit

## Scope
Audited all five relational tables in the supplied SQLite database and corresponding CSV files.

### Record counts
- patient_journey: **1,500**
- provider_master: **30**
- communication_logs: **6,025**
- treatment_outcomes: **554**
- country_reference: **12**

All five SQLite table counts match the CSV source counts.

## Key governance findings

1. **Keys:** all five designated business keys are non-null and unique in the supplied CSVs.
2. **Foreign-key reconciliation:** zero orphan references were detected across patient/provider/country relationships.
3. **SQLite constraints:** the database has `PRAGMA foreign_keys=0`, no declared foreign keys, and no indexes. The columns are stored as TEXT, including numeric and date fields. This is acceptable for a small analytical handoff but should be hardened for production.
4. **Missing satisfaction:** 946/1,500 records (63.1%) have missing `satisfaction_score`; missingness is structurally aligned with non-completed cases because satisfaction is only recorded for completed treatments.
5. **Missing communication delay:** 1,413/6,025 communication rows (23.5%) have missing `response_delay_hours`; all such rows have `response_sent=0`, so missingness means “no response” rather than an unknown numeric delay.
6. **Financial reconciliation:** all 554 completed patient records reconcile to `treatment_outcomes`; revenue and service cost totals match exactly, and `gross_margin_inr = revenue - cost` for every treatment outcome.
7. **Funnel tracking anomaly:** **229 completed patients have `quote_shared=0`**. The raw flag-based quote-to-treatment rate of 98.75% is therefore misleading as a sequential funnel KPI.

## Recommended controls
- Add typed columns and PK/FK constraints to the production SQLite/warehouse schema.
- Index patient/provider foreign keys.
- Preserve null semantics for unanswered communications.
- Treat satisfaction as a post-treatment outcome.
- Add a quote-stage completion validation rule so completed treatments cannot silently bypass quote tracking.
