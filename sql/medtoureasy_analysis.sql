-- MedTourEasy Patient Conversion & Provider Performance Intelligence
-- SQLite production-style analytics layer.
-- Numeric fields are stored as TEXT in the supplied database, so CAST is explicit.
-- KPI definitions follow the project PRD. Query 1 reports both raw stage flags and
-- the strict sequential completion count because 229 completed patients lack quote_shared=1.

-- Q1. Aggregate funnel conversion rates
WITH base AS (
    SELECT
        COUNT(*) AS inquiries,
        SUM(CAST(consultation_booked AS INTEGER)) AS consultations,
        SUM(CAST(quote_shared AS INTEGER)) AS quotes,
        SUM(CAST(treatment_completed AS INTEGER)) AS treatments,
        SUM(CASE WHEN CAST(treatment_completed AS INTEGER)=1
                  AND CAST(quote_shared AS INTEGER)=1 THEN 1 ELSE 0 END) AS strict_treatments
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
    ROUND(100.0 * strict_treatments / NULLIF(quotes,0),2) AS strict_quote_to_treatment_pct
FROM base;

-- Q2. Provider performance scorecard
WITH provider_cases AS (
    SELECT
        pj.provider_id,
        COUNT(*) AS total_assigned_leads,
        SUM(CAST(pj.treatment_completed AS INTEGER)) AS completed_cases,
        AVG(CAST(pj.response_time_hours AS REAL)) AS avg_response_time_hours,
        AVG(CAST(pj.engagement_score AS REAL)) AS avg_engagement_score,
        AVG(CASE WHEN CAST(pj.response_time_hours AS REAL) >
                      CAST(cr.baseline_response_expectation_hours AS REAL) THEN 1.0 ELSE 0.0 END) AS sla_breach_rate,
        AVG(CAST(pj.follow_up_completed AS REAL)) AS follow_up_completion_rate,
        AVG(CASE WHEN pj.satisfaction_score IS NOT NULL
                 THEN CAST(pj.satisfaction_score AS REAL) END) AS avg_satisfaction_score
    FROM patient_journey pj
    JOIN country_reference cr ON cr.country = pj.country
    GROUP BY pj.provider_id
),
margins AS (
    SELECT
        provider_id,
        SUM(CAST(actual_revenue_inr AS REAL) - CAST(service_cost_inr AS REAL)) AS total_gross_margin_inr
    FROM treatment_outcomes
    GROUP BY provider_id
)
SELECT
    p.provider_id,
    p.provider_name,
    pc.total_assigned_leads,
    pc.completed_cases,
    ROUND(1.0 * pc.completed_cases / NULLIF(pc.total_assigned_leads,0),4) AS conversion_rate,
    ROUND(pc.avg_response_time_hours,2) AS avg_response_time_hours,
    ROUND(pc.avg_engagement_score,2) AS avg_engagement_score,
    ROUND(1.0-pc.sla_breach_rate,4) AS sla_adherence_rate,
    ROUND(pc.follow_up_completion_rate,4) AS follow_up_completion_rate,
    ROUND(pc.avg_satisfaction_score,2) AS avg_satisfaction_score,
    COALESCE(m.total_gross_margin_inr,0) AS total_gross_margin_inr
FROM provider_cases pc
JOIN provider_master p ON p.provider_id = pc.provider_id
LEFT JOIN margins m ON m.provider_id = pc.provider_id
ORDER BY conversion_rate DESC, total_gross_margin_inr DESC;

-- Q3. Unit economics by treatment category
SELECT
    treatment_category,
    COUNT(*) AS leads,
    SUM(CAST(treatment_completed AS INTEGER)) AS completed_cases,
    SUM(CAST(estimated_case_value_inr AS REAL)) AS estimated_case_value_inr,
    SUM(CAST(actual_revenue_inr AS REAL)) AS actual_revenue_inr,
    SUM(CAST(service_cost_inr AS REAL)) AS service_cost_inr,
    SUM(CAST(actual_revenue_inr AS REAL)-CAST(service_cost_inr AS REAL)) AS gross_margin_inr,
    ROUND(1.0*SUM(CAST(treatment_completed AS INTEGER))/COUNT(*),4) AS completion_rate,
    ROUND(
        1.0*SUM(CAST(actual_revenue_inr AS REAL)-CAST(service_cost_inr AS REAL)) /
        NULLIF(SUM(CAST(treatment_completed AS INTEGER)),0), 2
    ) AS margin_per_completed_case
FROM patient_journey
GROUP BY treatment_category
ORDER BY gross_margin_inr DESC;

-- Q4. Coordinator SLA performance
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

-- Q5. Channel conversion efficiency
SELECT
    lead_source,
    COUNT(*) AS leads,
    SUM(CAST(consultation_booked AS INTEGER)) AS consultations,
    SUM(CAST(quote_shared AS INTEGER)) AS quotes,
    SUM(CAST(treatment_completed AS INTEGER)) AS completed_cases,
    ROUND(1.0*SUM(CAST(consultation_booked AS INTEGER))/COUNT(*),4) AS consultation_rate,
    ROUND(1.0*SUM(CAST(treatment_completed AS INTEGER))/COUNT(*),4) AS completion_rate,
    SUM(CAST(actual_revenue_inr AS REAL)-CAST(service_cost_inr AS REAL)) AS gross_margin_inr,
    ROUND(
        1.0*SUM(CAST(actual_revenue_inr AS REAL)-CAST(service_cost_inr AS REAL))/COUNT(*),2
    ) AS margin_per_lead
FROM patient_journey
GROUP BY lead_source
ORDER BY completion_rate DESC;

-- Q6. Country SLA and conversion
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

-- Q7. Drop-off distribution by stage and source
SELECT
    drop_off_stage,
    lead_source,
    COUNT(*) AS dropoff_cases,
    ROUND(100.0*COUNT(*) / SUM(COUNT(*)) OVER (),2) AS share_of_coded_dropoffs_pct
FROM patient_journey
WHERE CAST(drop_off_flag AS INTEGER)=1
GROUP BY drop_off_stage, lead_source
ORDER BY dropoff_cases DESC;

-- Q8. Monthly inquiry cohort conversion
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

-- Q9. Provider conversion rank using a window function
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
