-- =============================================================================
-- MedTourEasy Patient Conversion & Provider Performance Intelligence
-- SQLite Production-Style Analytics & Governance Layer
-- =============================================================================
-- Schema Note: Numeric fields are stored as TEXT in the supplied SQLite database,
-- so explicit CAST(... AS INTEGER/REAL) is used across all calculations.
-- KPI definitions strictly follow the MedTourEasy Corporate PRD.
-- Query 1 reports both raw stage flags and the strict sequential completion count
-- because 229 completed patients lack quote_shared=1.
-- =============================================================================

-- Q1. Aggregate Funnel Conversion Rates (Raw Flags vs. Strict Sequential)
WITH base AS (
    SELECT
        COUNT(*) AS inquiries,
        SUM(CAST(consultation_booked AS INTEGER)) AS consultations,
        SUM(CAST(quote_shared AS INTEGER)) AS quotes,
        SUM(CAST(treatment_completed AS INTEGER)) AS treatments,
        SUM(CASE WHEN CAST(treatment_completed AS INTEGER)=1
                  AND CAST(quote_shared AS INTEGER)=1 THEN 1 ELSE 0 END) AS strict_treatments,
        SUM(CASE WHEN CAST(treatment_completed AS INTEGER)=1
                  AND CAST(quote_shared AS INTEGER)=0 THEN 1 ELSE 0 END) AS unquoted_completions
    FROM patient_journey
)
SELECT
    inquiries,
    consultations,
    ROUND(100.0 * consultations / NULLIF(inquiries,0),2) AS consultation_conversion_pct,
    quotes,
    ROUND(100.0 * quotes / NULLIF(consultations,0),2) AS quote_from_consultation_pct,
    treatments,
    ROUND(100.0 * treatments / NULLIF(inquiries,0),2) AS recorded_treatment_completion_pct,
    strict_treatments,
    ROUND(100.0 * strict_treatments / NULLIF(quotes,0),2) AS strict_quote_to_treatment_pct,
    unquoted_completions
FROM base;

-- Q2. Provider Performance Scorecard & Margin per Lead
WITH provider_cases AS (
    SELECT
        pj.provider_id,
        COUNT(*) AS total_assigned_leads,
        SUM(CAST(pj.consultation_booked AS INTEGER)) AS consultation_bookings,
        SUM(CAST(pj.treatment_completed AS INTEGER)) AS completed_cases,
        AVG(CAST(pj.response_time_hours AS REAL)) AS avg_response_time_hours,
        AVG(CAST(pj.engagement_score AS REAL)) AS avg_engagement_score,
        AVG(CASE WHEN CAST(pj.response_time_hours AS REAL) >
                      CAST(cr.baseline_response_expectation_hours AS REAL) THEN 1.0 ELSE 0.0 END) AS sla_breach_rate,
        AVG(CAST(pj.follow_up_completed AS REAL)) AS follow_up_completion_rate,
        AVG(CASE WHEN pj.satisfaction_score IS NOT NULL AND pj.satisfaction_score != ''
                 THEN CAST(pj.satisfaction_score AS REAL) END) AS avg_satisfaction_score
    FROM patient_journey pj
    JOIN country_reference cr ON cr.country = pj.country
    GROUP BY pj.provider_id
),
margins AS (
    SELECT
        provider_id,
        SUM(CAST(actual_revenue_inr AS REAL)) AS total_revenue_inr,
        SUM(CAST(service_cost_inr AS REAL)) AS total_cost_inr,
        SUM(CAST(actual_revenue_inr AS REAL) - CAST(service_cost_inr AS REAL)) AS total_gross_margin_inr
    FROM treatment_outcomes
    GROUP BY provider_id
)
SELECT
    p.provider_id,
    p.provider_name,
    pc.total_assigned_leads,
    pc.consultation_bookings,
    pc.completed_cases,
    ROUND(1.0 * pc.completed_cases / NULLIF(pc.total_assigned_leads,0),4) AS conversion_rate,
    ROUND(pc.avg_response_time_hours,2) AS avg_response_time_hours,
    ROUND(pc.avg_engagement_score,2) AS avg_engagement_score,
    ROUND(1.0-pc.sla_breach_rate,4) AS sla_adherence_rate,
    ROUND(pc.follow_up_completion_rate,4) AS follow_up_completion_rate,
    ROUND(pc.avg_satisfaction_score,2) AS avg_satisfaction_score,
    COALESCE(m.total_revenue_inr,0) AS total_revenue_inr,
    COALESCE(m.total_cost_inr,0) AS total_cost_inr,
    COALESCE(m.total_gross_margin_inr,0) AS total_gross_margin_inr,
    ROUND(COALESCE(m.total_gross_margin_inr,0) / NULLIF(pc.total_assigned_leads,0), 2) AS margin_per_lead_inr
FROM provider_cases pc
JOIN provider_master p ON p.provider_id = pc.provider_id
LEFT JOIN margins m ON m.provider_id = pc.provider_id
ORDER BY conversion_rate DESC, total_gross_margin_inr DESC;

-- Q3. Unit Economics by Treatment Category
SELECT
    treatment_category,
    COUNT(*) AS leads,
    SUM(CAST(treatment_completed AS INTEGER)) AS completed_cases,
    SUM(CAST(estimated_case_value_inr AS REAL)) AS estimated_case_value_inr,
    SUM(CAST(actual_revenue_inr AS REAL)) AS actual_revenue_inr,
    SUM(CAST(service_cost_inr AS REAL)) AS service_cost_inr,
    SUM(CAST(actual_revenue_inr AS REAL)-CAST(service_cost_inr AS REAL)) AS gross_margin_inr,
    ROUND(
        100.0 * SUM(CAST(actual_revenue_inr AS REAL)-CAST(service_cost_inr AS REAL)) /
        NULLIF(SUM(CAST(actual_revenue_inr AS REAL)), 0), 2
    ) AS gross_margin_pct,
    ROUND(1.0*SUM(CAST(treatment_completed AS INTEGER))/COUNT(*),4) AS completion_rate,
    ROUND(
        1.0*SUM(CAST(actual_revenue_inr AS REAL)-CAST(service_cost_inr AS REAL)) /
        NULLIF(SUM(CAST(treatment_completed AS INTEGER)),0), 2
    ) AS margin_per_completed_case
FROM patient_journey
GROUP BY treatment_category
ORDER BY gross_margin_inr DESC;

-- Q4. Coordinator SLA Benchmarking
WITH coordinator AS (
    SELECT
        coordinator_id,
        COUNT(*) AS leads,
        SUM(CAST(consultation_booked AS INTEGER)) AS consultations,
        SUM(CAST(treatment_completed AS INTEGER)) AS completed_cases,
        SUM(CAST(follow_up_completed AS INTEGER)) AS completed_followups,
        AVG(CAST(response_time_hours AS REAL)) AS avg_response_hours,
        AVG(CASE WHEN CAST(response_time_hours AS REAL) >
                      CAST(cr.baseline_response_expectation_hours AS REAL) THEN 1.0 ELSE 0.0 END) AS sla_breach_rate
    FROM patient_journey pj
    JOIN country_reference cr ON cr.country = pj.country
    GROUP BY coordinator_id
)
SELECT *,
       ROUND(1.0*consultations/NULLIF(leads,0),4) AS consultation_rate,
       ROUND(1.0*completed_cases/NULLIF(leads,0),4) AS completion_rate,
       ROUND(1.0*completed_followups/NULLIF(leads,0),4) AS followup_rate,
       ROUND(1.0-sla_breach_rate,4) AS sla_adherence_rate
FROM coordinator
ORDER BY sla_breach_rate ASC, completion_rate DESC;

-- Q5. Acquisition Channel Conversion & Economics
SELECT
    lead_source,
    COUNT(*) AS leads,
    SUM(CAST(consultation_booked AS INTEGER)) AS consultations,
    SUM(CAST(quote_shared AS INTEGER)) AS quotes,
    SUM(CAST(treatment_completed AS INTEGER)) AS completed_cases,
    ROUND(1.0*SUM(CAST(consultation_booked AS INTEGER))/COUNT(*),4) AS consultation_rate,
    ROUND(1.0*SUM(CAST(treatment_completed AS INTEGER))/COUNT(*),4) AS completion_rate,
    SUM(CAST(actual_revenue_inr AS REAL)) AS revenue_inr,
    SUM(CAST(service_cost_inr AS REAL)) AS service_cost_inr,
    SUM(CAST(actual_revenue_inr AS REAL)-CAST(service_cost_inr AS REAL)) AS gross_margin_inr,
    ROUND(
        1.0*SUM(CAST(actual_revenue_inr AS REAL)-CAST(service_cost_inr AS REAL))/COUNT(*),2
    ) AS margin_per_lead
FROM patient_journey
GROUP BY lead_source
ORDER BY completion_rate DESC;

-- Q6. Country SLA Adherence & Market Priority Analysis
SELECT
    pj.country,
    COUNT(*) AS leads,
    CAST(cr.baseline_response_expectation_hours AS REAL) AS baseline_sla_hours,
    ROUND(AVG(CASE WHEN CAST(pj.response_time_hours AS REAL) >
                        CAST(cr.baseline_response_expectation_hours AS REAL) THEN 1.0 ELSE 0.0 END),4) AS sla_breach_rate,
    ROUND(AVG(CAST(pj.consultation_booked AS REAL)),4) AS consultation_rate,
    ROUND(AVG(CAST(pj.treatment_completed AS REAL)),4) AS completion_rate,
    CAST(cr.market_priority_score AS REAL) AS market_priority_score
FROM patient_journey pj
JOIN country_reference cr ON cr.country = pj.country
GROUP BY pj.country
ORDER BY sla_breach_rate DESC;

-- Q7. Drop-off Distribution by Stage and Source (with Window Function Share)
SELECT
    drop_off_stage,
    lead_source,
    COUNT(*) AS dropoff_cases,
    SUM(CAST(estimated_case_value_inr AS REAL)) AS dropoff_case_value_exposure_inr,
    ROUND(100.0*COUNT(*) / SUM(COUNT(*)) OVER (),2) AS share_of_coded_dropoffs_pct
FROM patient_journey
WHERE CAST(drop_off_flag AS INTEGER)=1
GROUP BY drop_off_stage, lead_source
ORDER BY dropoff_cases DESC;

-- Q8. Monthly Inquiry Cohort Conversion
WITH monthly AS (
    SELECT
        substr(inquiry_date,1,7) AS inquiry_month,
        COUNT(*) AS inquiries,
        SUM(CAST(consultation_booked AS INTEGER)) AS consultations,
        SUM(CAST(quote_shared AS INTEGER)) AS quotes,
        SUM(CAST(treatment_completed AS INTEGER)) AS treatments
    FROM patient_journey
    GROUP BY substr(inquiry_date,1,7)
)
SELECT
    inquiry_month,
    inquiries,
    consultations,
    quotes,
    treatments,
    ROUND(1.0*consultations/NULLIF(inquiries,0),4) AS consultation_rate,
    ROUND(1.0*quotes/NULLIF(inquiries,0),4) AS quote_rate,
    ROUND(1.0*treatments/NULLIF(inquiries,0),4) AS completion_rate,
    ROUND(100.0*treatments/NULLIF(inquiries,0),2) AS completion_pct
FROM monthly
ORDER BY inquiry_month;

-- Q9. Provider Conversion Rank Using Window Functions
WITH provider_perf AS (
    SELECT
        provider_id,
        COUNT(*) AS leads,
        SUM(CAST(treatment_completed AS INTEGER)) AS completed,
        AVG(CAST(response_time_hours AS REAL)) AS avg_response_hours
    FROM patient_journey
    GROUP BY provider_id
)
SELECT
    provider_id,
    leads,
    completed,
    ROUND(1.0*completed/NULLIF(leads,0),4) AS conversion_rate,
    ROUND(avg_response_hours,2) AS avg_response_hours,
    DENSE_RANK() OVER (ORDER BY 1.0*completed/NULLIF(leads,0) DESC) AS conversion_rank
FROM provider_perf
ORDER BY conversion_rank, provider_id;

-- Q10. Rule-Based Patient Persona Segmentation in SQL (Mirrors K-Means Personas)
WITH patient_segments AS (
    SELECT
        patient_id,
        CAST(intent_score AS REAL) AS intent_score,
        CAST(engagement_score AS REAL) AS engagement_score,
        CAST(response_time_hours AS REAL) AS response_time_hours,
        CAST(estimated_case_value_inr AS REAL) AS estimated_case_value_inr,
        CAST(consultation_booked AS INTEGER) AS consultation_booked,
        CAST(treatment_completed AS INTEGER) AS treatment_completed,
        CAST(drop_off_flag AS INTEGER) AS drop_off_flag,
        CAST(actual_revenue_inr AS REAL) - CAST(service_cost_inr AS REAL) AS gross_margin_inr,
        CASE
            WHEN CAST(estimated_case_value_inr AS REAL) >= 550000 THEN 'High-Value At-Risk (Rule-Based)'
            WHEN CAST(engagement_score AS REAL) >= 52.0 AND CAST(intent_score AS REAL) >= 60.0 THEN 'High-Intent Converters (Rule-Based)'
            ELSE 'High-Risk Disengaged (Rule-Based)'
        END AS sql_segment
    FROM patient_journey
)
SELECT
    sql_segment,
    COUNT(*) AS patients,
    ROUND(AVG(intent_score), 2) AS avg_intent_score,
    ROUND(AVG(engagement_score), 2) AS avg_engagement_score,
    ROUND(AVG(response_time_hours), 2) AS avg_response_time_hours,
    ROUND(AVG(estimated_case_value_inr), 0) AS avg_case_value_inr,
    ROUND(AVG(consultation_booked), 4) AS consultation_rate,
    ROUND(AVG(treatment_completed), 4) AS completion_rate,
    ROUND(AVG(drop_off_flag), 4) AS dropoff_rate,
    ROUND(SUM(gross_margin_inr), 0) AS total_gross_margin_inr
FROM patient_segments
GROUP BY sql_segment
ORDER BY completion_rate DESC;

-- Q11. Automated Data Quality, Financial Reconciliation & Funnel Integrity Audit
SELECT
    'Orphan Provider IDs in patient_journey' AS check_name,
    COUNT(*) AS issue_count
FROM patient_journey pj
LEFT JOIN provider_master pm ON pm.provider_id = pj.provider_id
WHERE pm.provider_id IS NULL
UNION ALL
SELECT
    'Orphan Patient IDs in treatment_outcomes' AS check_name,
    COUNT(*) AS issue_count
FROM treatment_outcomes to_tbl
LEFT JOIN patient_journey pj ON pj.patient_id = to_tbl.patient_id
WHERE pj.patient_id IS NULL
UNION ALL
SELECT
    'Revenue Reconciliation Mismatch (patient_journey vs treatment_outcomes)' AS check_name,
    CAST(
        (SELECT SUM(CAST(actual_revenue_inr AS INTEGER)) FROM patient_journey WHERE CAST(treatment_completed AS INTEGER)=1) -
        (SELECT SUM(CAST(actual_revenue_inr AS INTEGER)) FROM treatment_outcomes)
    AS INTEGER) AS issue_count
UNION ALL
SELECT
    'Completed Treatments Missing Quote Shared Flag (Stage Anomaly)' AS check_name,
    COUNT(*) AS issue_count
FROM patient_journey
WHERE CAST(treatment_completed AS INTEGER) = 1
  AND CAST(quote_shared AS INTEGER) = 0;
