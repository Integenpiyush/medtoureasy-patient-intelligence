# Assumptions Log

1. **Patient journey is the base population:** 1,500 unique `patient_id` records.
2. **Treatment outcome linkage:** `treatment_outcomes.patient_id` is treated as the outcome-side completion record; it reconciles exactly to the 554 treatment-completed flags.
3. **Sequential funnel anomaly:** 229 completed patients have `quote_shared=0`. Raw flags are preserved; a strict sequential funnel is reported separately.
4. **SLA breach:** `response_time_hours > country baseline_response_expectation_hours`.
5. **Financial margin:** `actual_revenue_inr - service_cost_inr`.
6. **Satisfaction:** considered post-treatment and excluded from the pre-treatment ML feature set.
7. **Communication features:** only communication activity in the first 72 hours after inquiry is used for ML to reduce target leakage.
8. **Economic scenarios:** recovery values are scenarios based on converting a percentage of drop-off estimated case value; they are not causal forecasts.
9. **Provider Intelligence Score:** 30% conversion, 20% SLA adherence, 15% follow-up completion, 15% satisfaction, 20% margin per lead. Component scores are normalized to the observed provider range.
10. **Statistical interpretation:** hypothesis tests support association; they do not establish that SLA breach causes non-conversion.
