# Executive Recommendation Memo: MedTourEasy Patient Conversion & Provider Performance Intelligence

**Prepared For:** Executive Management, Operations Leadership & Partner Hospital Strategy  
**Scope:** End-to-End Audit & Intelligence System across 1,500 International Patient Journeys, 30 Partner Hospitals, 15 Care Coordinators, and 12 Source Markets  

---

## 1. Business Problem

MedTourEasy facilitates international medical travel across high-acuity and elective procedures (Oncology, Transplant Evaluation, Neurology, Cardiology, Orthopedics, Bariatric Surgery, Fertility, Cosmetic Surgery, and Dental). Prior to this workstream, operational visibility suffered from four structural challenges:

1. **Fragmented Patient Journey Tracking:** Patient progression across inquiry, first response, consultation booking, quote sharing, treatment completion, and post-treatment follow-up lived in separate tables without unified stage-integrity checks.
2. **Delayed Risk Identification:** Care coordinators lacked an objective, pre-treatment risk score to identify high-value or disengaged international leads before they dropped out of the funnel.
3. **Un-benchmarked Provider & Coordinator SLAs:** Partner hospitals were evaluated primarily on raw volume or historical anecdotes rather than a balanced composite of conversion efficiency, country-specific response-time SLA adherence, follow-up discipline, patient satisfaction, and gross margin per lead.
4. **Unreconciled Unit Economics:** Leadership needed a single source of truth reconciling lead-level estimated case value exposure against actual realized revenue and service costs.

---

## 2. Dataset & Methodology

We audited and reconciled five relational tables across CSV and SQLite (`mte_patient_intelligence.db`):

| Table | Rows | Primary Key | Key Entities & Metrics |
|---|---:|---|---|
| `patient_journey` | **1,500** | `patient_id` | Inquiry date, source market, specialty, provider/coordinator assignment, intent & engagement scores, response time, stage flags, drop-off reason, financial outcomes |
| `provider_master` | **30** | `provider_id` | Partner hospital metadata, bed capacity, international desk status, historical conversion rates, pricing tier |
| `communication_logs` | **6,025** | `communication_id` | Timestamped touchpoints across 6 channels, sender role, response flag, response delay hours, follow-up status |
| `treatment_outcomes` | **554** | `patient_id` | Treatment date, length of stay, actual revenue (`INR`), service cost (`INR`), gross margin (`INR`), 30-day readmission flag, follow-up rating |
| `country_reference` | **12** | `country` | Source region, travel lead time, medical visa requirement, baseline response expectation (`6h`, `8h`, or `12h`), market priority score |

### Methodological Pillars
- **Data Governance First:** Automated primary-key, foreign-key (`0` orphans across all 6 relational links), CSV-vs-SQLite normalization, and financial reconciliation checks (`₹248,325,245` revenue and `₹111,514,356` gross margin match to the exact rupee across `patient_journey` and `treatment_outcomes`).
- **Dual Funnel Accounting:** Explicit separation of raw stage flags from strict sequential stage progression after discovering a major quote-stage tracking anomaly.
- **Parametric & Non-Parametric Hypothesis Testing:** Chi-square test of independence ($\chi^2$) with Cramér's $V$ and Welch's unequal-variance $t$-test with Cohen's $d$ and 95% confidence intervals.
- **Leakage-Free Supervised Machine Learning:** 80/20 stratified train-test split ($N_{\text{train}}=1,200, N_{\text{test}}=300$) comparing an interpretable **Logistic Regression** baseline against a tuned **Random Forest** classifier using strictly pre-cutoff features (restricting communication logs to the first **72 hours** post-inquiry and excluding all post-treatment variables).
- **Unsupervised Behavioral Segmentation:** Standardized K-Means clustering ($k=3$) validated via Silhouette Score and Davies-Bouldin Index to map leads into operational personas.

---

## 3. Key Funnel Findings & Stage-Integrity Audit

### Raw Flag Funnel vs. Strict Sequential Funnel

| Funnel Stage | Denominator | Raw Flag Count | Raw Conversion (%) | Strict Sequential Count | Strict Conversion (%) |
|---|---:|---:|---:|---:|---:|
| **1. Total Inquiries** | 1,500 | **1,500** | 100.00% | **1,500** | 100.00% |
| **2. Consultations Booked** | 1,500 | **984** | 65.60% | **984** | 65.60% |
| **3. Quotes Shared** | 984 | **561** | 57.01% | **561** | 57.01% |
| **4. Treatments Completed** | 561 | **554** | *98.75% (Artifact)* | **325** | **57.93% (True Sequential)** |

> [!IMPORTANT]
> **Critical Governance Discovery — 229 Unquoted Completions:**  
> Exactly **229 patients** have `treatment_completed = 1` while `quote_shared = 0` (including 15 who also have `consultation_booked = 0`, representing direct/expedited hospital admissions or offline quote sharing). Dividing total completions (`554`) by recorded quotes (`561`) produces an artificial **98.75%** quote-to-treatment ratio. When restricted to patients with a recorded quote flag (`325 / 561`), the true sequential quote-to-treatment conversion rate is **57.93%**. Both metrics are reported transparently so management does not misinterpret CRM logging bypasses as near-100% quote acceptance.

### Drop-Off Leakage Breakdown
- **Top-of-Funnel Non-Conversion:** **516 inquiries (34.4%)** never book an initial consultation, and **423 booked consultations (43.0%)** never receive a recorded quote.
- **Explicitly Coded Drop-Offs (`drop_off_flag = 1`):** **350 patients** carry explicit drop-off coding totaling **₹166.51M** in estimated case value exposure:
  - **By Stage:** Inquiry (**103 cases**, 29.4%), First Response (**89 cases**, 25.4%), Consultation (**55 cases**, 15.7%), Treatment Plan (**49 cases**, 14.0%), Quote Shared (**43 cases**, 12.3%), Travel Planning (**11 cases**, 3.1%). Over **54.8%** of coded drop-offs occur before or during first response.
  - **By Primary Reason:** No follow-up (**66**), Cost concern (**62**), Response delay (**60**), Language barrier (**34**), Chose local hospital (**31**), Travel/visa issue (**29**), Clinical ineligibility (**25**), Insurance/payment issue (**22**), Family decision delay (**21**).

---

## 4. Statistical SLA Findings

Each source country has a defined baseline response expectation (`6h` for Nigeria, Nepal, Sri Lanka; `8h` for India, Malaysia, Philippines, Tanzania, UAE; `12h` for Bangladesh, Kenya, Oman, Thailand). Across all 1,500 inquiries, **1,242 cases (82.8%)** breached their country-specific SLA.

| Statistical Metric | Observed Result | Interpretation |
|---|---:|---|
| **SLA-Compliant Inquiries (`sla_breach = False`)** | **258 (17.2%)** | Baseline compliant cohort |
| **SLA-Breached Inquiries (`sla_breach = True`)** | **1,242 (82.8%)** | Widespread first-response bottleneck |
| **Consultation Rate (SLA Compliant)** | **79.46%** (205 / 258) | Strong conversion when SLA is met |
| **Consultation Rate (SLA Breached)** | **62.72%** (779 / 1,242) | Material drop in booking propensity |
| **Absolute Consultation-Rate Gap** | **-16.74 pp** | 95% CI: `[-22.39 pp, -11.09 pp]` |
| **Chi-Square Statistic ($\chi^2$, $\text{dof}=1$)** | **25.78** ($p = 3.83 \times 10^{-7}$) | Statistically significant association (Cramér's $V = 0.131$) |
| **Mean First Response Time (Booked vs. Not Booked)** | **15.77h vs. 19.40h** | Difference: **-3.63h** (95% CI: `[-4.53h, -2.74h]`) |
| **Welch's Two-Sample $t$-Test** | **$t = -7.96$** ($p = 4.84 \times 10^{-15}$) | Medium-to-strong standardized difference (Cohen's $d = -0.431$) |

**Methodological Note (Association vs. Causation):** Because the dataset is observational, these tests prove that slower response times are strongly *associated* with lower consultation booking, not that SLA breaches *solely cause* non-conversion. Controlled routing experiments (A/B testing rapid-response triage desks) are recommended to quantify causal lift.

---

## 5. Provider, Coordinator & Channel Intelligence

### Provider Performance Scorecard (30 Partner Hospitals)
Rather than ranking hospitals solely on raw conversion (which penalizes hospitals taking complex cases or ignores slow response times), we implemented the PRD's weighted **Provider Intelligence Score (0–100)**:
- **30%** Conversion Rate Score (min-max normalized)
- **20%** SLA Adherence Rate (`1 - sla_breach_rate`)
- **15%** Follow-up Completion Rate
- **15%** Patient Satisfaction Score (`avg_satisfaction_score * 10`)
- **20%** Gross Margin per Lead Score (min-max normalized)

| Rank | Provider ID | Assigned Leads | Completed Cases | Conversion Rate | Avg Response (h) | SLA Adherence | Gross Margin (`INR`) | Margin / Lead (`INR`) | Intelligence Score | Operational Archetype |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **1** | **PVD-020** | 55 | 29 | **52.73%** | **5.85h** | **72.73%** | ₹5.84M | ₹106,255 | **80.78** | **Gold Benchmark:** Fastest response, #1 conversion |
| **2** | **PVD-008** | 55 | 28 | **50.91%** | 10.28h | 45.45% | **₹6.15M** | **₹111,739** | **71.77** | **High-Margin Leader:** Highest margin/lead & satisfaction (8.23) |
| **3** | **PVD-007** | 50 | 26 | **52.00%** | 15.41h | 18.00% | ₹5.45M | ₹109,057 | **67.00** | **High Conv / Low SLA:** Strong clinical close, slow intake desk |
| **4** | **PVD-015** | 56 | 26 | **46.43%** | 12.51h | 30.36% | ₹5.98M | ₹106,709 | **64.46** | **Balanced Tier-1 Partner** |
| **5** | **PVD-001** | 55 | 26 | **47.27%** | 16.78h | 10.91% | ₹5.50M | ₹99,932 | **60.20** | **High Volume / SLA Remediation Target** |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| **28** | **PVD-014** | 52 | 12 | 23.08% | 16.97h | 9.62% | ₹2.35M | ₹45,127 | **16.89** | **Underperforming:** High drop-off, low follow-up (9.6%) |
| **29** | **PVD-013** | 50 | 12 | 24.00% | 25.91h | 0.00% | ₹2.30M | ₹46,037 | **16.02** | **Critical SLA Failure:** 100% SLA breach rate |
| **30** | **PVD-023** | 46 | 11 | 23.91% | 25.21h | 0.00% | ₹1.64M | ₹35,606 | **13.06** | **Bottom Performer:** Reallocate lead volume |

### Coordinator SLA Benchmarking (15 Care Coordinators)
- **Top Converters:** `COORD-06` (**42.34%** completion on 111 leads, **72.07%** consultation rate) and `COORD-03` (**41.67%** completion on 96 leads).
- **Best SLA Adherence:** `COORD-12` (**23.23%** SLA adherence, **16.87h** avg response) and `COORD-14` (**20.73%** SLA adherence, **16.14h** avg response).
- **Coaching Priority:** `COORD-09` (**30.68%** completion, **18.34h** avg response, **86.36%** SLA breach) and `COORD-10` (**31.00%** completion, **88.00%** SLA breach).

### Acquisition Channel Efficiency (6 Channels)
| Channel | Leads | Consult Rate | Completion Rate | Coded Drop-Off Rate | Realized Gross Margin | Margin per Lead | Strategic Action |
|---|---:|---:|---:|---:|---:|---:|---|
| **Phone** | 244 | 67.62% | 38.52% | 25.41% | ₹20.11M | **₹82,420** | **Highest unit value:** Protect phone desk staffing |
| **Email** | 238 | 61.76% | **39.92%** | **18.91%** | ₹19.47M | **₹81,826** | **Highest completion & lowest drop-off:** High-intent detailed inquiries |
| **WhatsApp** | 272 | 69.12% | 38.60% | 20.59% | **₹21.02M** | ₹77,280 | **Largest volume & total margin:** Core conversational channel |
| **Chatbot** | 254 | **70.08%** | 36.61% | 22.44% | ₹19.25M | ₹75,779 | **Best initial booking rate:** Improve post-consultation handoff |
| **Referral Partner** | 246 | 62.60% | 33.33% | 25.61% | ₹15.92M | ₹64,706 | **Underperforming B2B channel:** Audit partner lead qualification |
| **Web Form** | 246 | 61.79% | 34.55% | **27.24%** | ₹15.74M | ₹63,998 | **Highest drop-off rate:** Replace static wait times with instant callback |

---

## 6. Supervised Machine Learning Results

### Leakage Prevention Architecture
To ensure the model is deployable at the early triage stage (**72 hours post-inquiry**), we enforced strict temporal and causal guardrails:
- **Excluded Post-Treatment & Outcome Fields:** `actual_revenue_inr`, `service_cost_inr`, `gross_margin_inr`, `satisfaction_score` (only populated for the 554 completed cases), and all `treatment_outcomes` fields.
- **Excluded Funnel-State Flags:** `consultation_booked`, `quote_shared`, `follow_up_completed`, `current_stage`, `drop_off_flag`, `drop_off_stage`, and `reason_for_drop_off`.
- **72-Hour Communication Cutoff:** Only `communication_logs` occurring within $0 \le t - t_{\text{inquiry}} \le 72\text{ hours}$ were aggregated (`early_interactions`, `early_response_rate`, `early_avg_response_delay`, `early_followup_completed`).

### Model Performance Comparison (80/20 Stratified Test Set, $N_{\text{test}} = 300$)

| Model | ROC-AUC | Precision | Recall | F1-Score | True Neg (TN) | False Pos (FP) | False Neg (FN) | True Pos (TP) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Logistic Regression (Balanced)** | **0.8193** | 0.6187 | **0.7748** | 0.6880 | 136 | 53 | 25 | 86 |
| **Random Forest (Balanced, Tuned)** | **0.8695** | **0.7723** | 0.7027 | **0.7358** | 166 | 23 | 33 | 78 |

### Top Predictive Drivers (Random Forest Feature Importance)
1. **`engagement_score` (29.63%):** Early patient responsiveness and document sharing is the single strongest predictor of completion.
2. **`estimated_case_value_inr` (12.96%):** Captures clinical complexity and financial commitment barriers.
3. **`intent_score` (7.53%):** Initial clinical readiness at inquiry.
4. **`response_time_hours` (7.42%):** First-response latency directly erodes conversion probability.
5. **`early_avg_response_delay` (4.70%):** Average turnaround time on touchpoints during the first 72 hours.
6. **Provider Historical Baselines (`follow_up_completion_rate` 3.41%, `historical_consultation_conversion_rate` 2.91%, `avg_first_response_hours` 2.65%, `satisfaction_index` 2.45%):** Partner hospital capability materially shifts patient conversion.

### Operational Threshold Selection (Precision vs. Recall Trade-Off)
In international medical travel, a **False Negative** (failing to intervene on a viable patient who subsequently drops off) forfeits an average of **₹201,290 in gross margin per completed case**, whereas a **False Positive** (assigning a coordinator to a priority follow-up call) costs minutes of coordinator time. Lowering the Random Forest decision threshold from `0.50` to **`0.40`** boosts **Recall from 70.27% to 78.38%** while maintaining **67.97% Precision** and **0.7280 F1-score**.

---

## 7. Patient Personas (K-Means Segmentation)

Standardized K-Means clustering ($k=3$, `random_state=42`) on `intent_score`, `response_time_hours`, `engagement_score`, and `estimated_case_value_inr` partitions the 1,500 patients into three distinct operational personas:

| Cluster | Persona Name | Patients | Avg Intent | Avg Response (h) | Avg Engagement | Avg Case Value (`INR`) | Consult Rate | Completion Rate | Drop-Off Rate | Realized Gross Margin |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **0** | **High-Risk Disengaged** | **503** (33.5%) | 45.63 | **19.76h** | 32.07 | ₹402,100 | 45.13% | **14.71%** | **37.18%** | ₹12.74M |
| **1** | **High-Intent Converters** | **571** (38.1%) | **75.27** | **15.03h** | **69.70** | ₹327,005 | **81.96%** | **60.25%** | **10.16%** | **₹52.20M** |
| **2** | **High-Value At-Risk** | **426** (28.4%) | 63.13 | 16.43h | 55.49 | **₹716,827** | 67.84% | **31.92%** | **24.65%** | **₹46.58M** |

### Operational Playbook by Persona
- **High-Value At-Risk (426 patients, ₹716.8k avg case value):** Highest revenue density per patient but nearly **1 in 4 explicitly drop off** (31.9% completion vs 60.2% for converters). **Action:** Mandatory <4-hour senior coordinator assignment, routing to top-5 Intelligence Score providers (`PVD-020`, `PVD-008`, `PVD-015`), itemized multi-currency quote transparency, and dedicated medical-visa concierge support.
- **High-Intent Converters (571 patients, 60.2% completion):** Self-motivated leads generating ₹52.20M in gross margin. **Action:** Streamline consultation-to-quote velocity and automate routine travel/visa checklists so coordinator bandwidth isn't bottlenecked.
- **High-Risk Disengaged (503 patients, 14.7% completion, 19.8h avg response):** Suffers from severe initial response delays and low engagement. **Action:** Deploy automated instant WhatsApp/Chatbot triage to qualify budget and language needs within 1 hour of inquiry; escalate to human coordinators only after initial re-engagement is confirmed.

---

## 8. Financial Impact & Scenario Analysis

### Realized Baseline Financials (Reconciled Across Tables)
- **Completed Treatments:** `554` patients (`36.93%` of inquiries)
- **Observed Gross Revenue:** **₹248,325,245** (`₹248.33M`, avg `₹448,241` per completed case)
- **Observed Service Cost:** **₹136,810,889** (`₹136.81M`, avg `₹246,951` per completed case)
- **Observed Gross Margin:** **₹111,514,356** (`₹111.51M`, **44.91%** realized gross margin rate; `₹201,289` margin per completed case)
- **Highest-Margin Specialties:** Transplant Evaluation (**₹22.24M** total margin, **₹411.9k** margin/case), Oncology (**₹21.77M** total margin, **₹298.3k** margin/case), and Neurology (**₹16.26M** total margin, **₹232.2k** margin/case).

### Drop-Off Exposure & Scenario Estimates
The **350 explicitly coded drop-offs** represent **₹166,511,306 (`₹166.51M`)** in estimated case value exposure (with the top 20% of drop-offs alone accounting for **₹54.40M**).

> [!WARNING]
> **Financial Governance Note:** Drop-off estimated case value exposure is **not** guaranteed or automatically recoverable revenue. The figures below are **hypothetical planning scenarios** assuming a given percentage of drop-off case value converts at the observed completed-case gross margin rate of **44.9066%**.

| Financial Metric / Planning Scenario | Amount (`INR`) | Amount (`₹ Millions`) | Basis & Underlying Assumptions |
|---|---:|---:|---|
| **Observed Gross Revenue** | ₹248,325,245 | **₹248.33M** | Observed across 554 completed treatments |
| **Observed Service Cost** | ₹136,810,889 | **₹136.81M** | Observed across 554 completed treatments |
| **Observed Gross Margin (44.91%)** | ₹111,514,356 | **₹111.51M** | Exact match between `patient_journey` & `treatment_outcomes` |
| **Coded Drop-Off Case Value Exposure** | ₹166,511,306 | **₹166.51M** | Sum of `estimated_case_value_inr` for 350 coded drop-offs |
| **Top 20% High-Value Drop-Off Exposure** | ₹54,398,190 | **₹54.40M** | Top 70 coded drop-offs ranked by estimated case value |
| **Conservative Recovery Scenario (5%)** | ₹8,325,565 | **₹8.33M Rev / ₹3.74M Margin** | Scenario: 5% of drop-off exposure converts at 44.91% margin |
| **Base Case Recovery Scenario (10%)** | ₹16,651,131 | **₹16.65M Rev / ₹7.48M Margin** | Scenario: 10% of drop-off exposure converts at 44.91% margin |
| **Stretch Recovery Scenario (20%)** | ₹33,302,261 | **₹33.30M Rev / ₹14.95M Margin** | Scenario: 20% of drop-off exposure converts at 44.91% margin |

---

## 9. Recommended Operational Interventions & KPI Ownership

| Priority | Owner | Intervention | Target Cohort / System | Measurable KPI & Target |
|---:|---|---|---|---|
| **P0** | **Data Engineering & CRM Lead** | **Enforce Mandatory Quote-Stage Validation:** Block CRM status transitions to `Treatment Completed` unless a valid `quote_shared` record and timestamp exist. Migrate SQLite `TEXT` columns to typed schema with `FOREIGN KEY` constraints. | All 1,500+ patient records & CRM pipeline | Reduce unquoted completions from **229 (41.3% of completions)** to **0%** |
| **P0** | **Operations Lead** | **Country-Tiered First-Response Auto-Routing:** Implement automated SLA countdown alerts at 50% of country baseline (`3h` for 6h markets: Nigeria, Nepal, Sri Lanka; `4h` for 8h markets). | All incoming inquiries (especially 6h & 8h SLA markets) | Reduce SLA breach rate from **82.8%** to **<35.0%**; lift consultation rate from **65.6% to >72%** |
| **P1** | **Coordinator Manager** | **Deploy 72-Hour ML Risk & Persona Triage:** Score every active lead at hour 72 using the Random Forest model (`threshold = 0.40`) combined with K-Means persona tags. Escalate **High-Value At-Risk** leads (`case value > ₹550k`) to senior coordinators (`COORD-06`, `COORD-03`). | 426 High-Value At-Risk patients & 350 drop-off-prone leads | Achieve **>78% recall** on completion propensity; recover **5%–10% (₹3.7M–₹7.5M margin)** of drop-off exposure |
| **P1** | **Provider Partnerships** | **Reallocate Volume via Provider Intelligence Score:** Shift incremental Oncology, Transplant, and Neurology referrals toward Tier-1 benchmarks (`PVD-020`, `PVD-008`, `PVD-015`). Place bottom-5 providers (`PVD-023`, `PVD-013`, `PVD-014`, `PVD-028`, `PVD-025` — all near 0%–10% SLA adherence) on 60-day SLA remediation plans. | 30 Partner Hospitals | Lift network-wide treatment conversion from **36.9% to >41.0%** and avg margin/lead above **₹85,000** |
| **P2** | **Growth & Channel Lead** | **Fix Web Form & Referral Partner Friction:** Trigger instant automated WhatsApp/Phone callback within 15 minutes of `Web Form` submission (currently 27.2% drop-off rate) and audit `Referral Partner` lead quality (33.3% completion). | Web Form (246 leads) & Referral Partner (246 leads) | Reduce Web Form drop-off rate from **27.2% to <20.0%** |

---

## 10. Limitations & Next Steps

1. **Observational Study Design:** The 16.74 pp consultation gap between SLA-compliant and SLA-breached inquiries reflects observational association. Next step: run a **randomized controlled trial (RCT)** assigning 50% of incoming Web Form and Referral Partner leads to a dedicated rapid-response (<2h) desk to measure true causal conversion lift.
2. **Quote-Stage Tracking Gap:** Until the 229 unquoted completion records are backfilled from hospital billing/email logs, stage-wise quote-to-treatment analysis must always report both raw flags (`98.75%`) and strict sequential conversion (`57.93%`).
3. **Post-Treatment Satisfaction Missingness:** `satisfaction_score` is only captured for completed treatments (`554 / 1,500`). Introducing a short pulse survey after consultation or quote sharing would capture sentiment among non-converting patients and sharpen early drop-off diagnosis.
4. **Probability Calibration & Drift Monitoring:** As operational interventions reduce SLA breaches, the distribution of `response_time_hours` and `early_avg_response_delay` will shift, requiring quarterly retraining and isotonic/Platt probability calibration of the Random Forest model.
