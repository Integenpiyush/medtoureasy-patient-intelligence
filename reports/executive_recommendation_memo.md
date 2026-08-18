# Executive Recommendation Memo

## 1. Executive summary
The 1,500-patient dataset shows a **65.6% consultation booking rate** and **36.9% recorded treatment completion rate**. The largest operational signal is response speed: **82.8% of inquiries breach their country-specific response baseline**, and breached cases book consultations at **62.7% vs 79.5%** for non-breached cases. The association is statistically significant (χ²=25.78, p=3.83e-07); the response-time mean difference is also significant (Welch t=-7.96, p=4.84e-15).

A second priority is data governance: **229 completed cases lack a quote flag**, which inflates the apparent quote-to-treatment rate to 98.75%. The strict sequential view is **325/561 = 57.9%**.

## 2. Funnel and bottlenecks
- 1,500 inquiries → 984 consultations → 561 quotes → 554 recorded completions.
- 516 inquiries do not book a consultation.
- 350 cases are explicitly coded as drop-offs.
- Largest coded drop-off stages: Inquiry (103), First Response (89), Consultation (55).
- Leading coded reasons: No follow-up (66), Cost concern (62), Response delay (60).
- Highest coded drop-off rate by source: Web Form (27.2%), followed by Referral Partner and Phone.

## 3. Provider and channel implications
The provider scorecard should not rank on conversion alone. PVD-020 ranks first on the documented composite because it combines strong conversion, reasonable SLA adherence, follow-up, satisfaction and margin. PVD-007 has high conversion but weak SLA adherence, making it a targeted workflow-improvement candidate rather than a pure best-practice benchmark.

Channel-wise, Phone has the highest margin per lead (₹82,420), while Email has the highest recorded completion rate (39.9%). Web Form has the lowest consultation rate (61.8%) and should receive funnel-friction analysis.

## 4. Predictive risk model
| Model | ROC-AUC | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.8193 | 0.6187 | 0.7748 | 0.6880 |
| Random Forest | 0.8695 | 0.7723 | 0.7027 | 0.7358 |

Top Random Forest drivers:
1. Engagement score
2. Estimated case value
3. Intent score
4. Response time
5. Early average response delay

For intervention workflows, a lower classification threshold can improve recall. At threshold 0.40, recall is approximately 78.4%; this is preferable when the cost of missing a high-risk patient is larger than the cost of reviewing additional cases.

## 5. Patient personas
- **High-Risk Disengaged:** 503 patients; lowest engagement and completion. Action: immediate coordinator ownership, rapid re-contact, reason-code resolution.
- **High-Intent Converters:** 571 patients; strongest intent/engagement and completion. Action: protect SLA and accelerate consultation/quote turnaround.
- **High-Value At-Risk:** 426 patients; highest average case value but materially lower completion than converters. Action: senior coordinator escalation and provider matching.

## 6. Ownership and KPI framework
| Owner | Action | KPI |
|---|---|---|
| Operations Lead | Reduce first-response SLA breaches | SLA breach rate; median response time |
| Coordinator Manager | Prioritize high-risk patients | Risk-model recall; follow-up completion |
| Provider Partnerships | Benchmark low-SLA/high-conversion providers | Provider SLA adherence; conversion |
| Growth / Channel Lead | Fix Web Form and Referral Partner funnel friction | Consultation and completion rate |
| Data Governance | Repair quote-stage tracking | % completed cases with valid quote flag |
| Finance / Strategy | Monitor recovery economics | Gross margin recovered from reactivated cases |

## 7. Quantified economic opportunity
Observed completed-case gross margin is **₹111.5M**. Explicitly coded drop-offs carry **₹166.5M** in estimated case-value exposure.

A **10% recovery scenario** would imply **₹16.7M of additional revenue** and approximately **₹7.5M gross margin** if the observed 44.9% completed-case margin rate held. This is a scenario, not a forecast or causal estimate.

## 8. Risks and mitigations
- **Observational data:** do not interpret SLA association as causal; run controlled workflow experiments before claiming incremental lift.
- **Quote-stage data quality:** fix stage capture before using quote-to-treatment as a management KPI.
- **Post-treatment leakage:** exclude satisfaction and future communication from pre-treatment modeling.
- **Class imbalance:** retain stratification and report precision/recall alongside ROC-AUC.
- **Threshold risk:** validate operational capacity before choosing a risk intervention threshold.
