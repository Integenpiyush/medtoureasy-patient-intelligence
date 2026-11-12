# MedTourEasy — Resume-Aligned Interview Preparation Strategy (3 Tiers + Bullet-by-Bullet Defense)

## Your Exact Resume Entry

> **Data Science & Analytics Intern | MedTourEasy** *(May'26 – July'26)*
> - Engineered Python/SQL pipeline across 1,500 patient journeys and 5 datasets for funnel and provider analytics.
> - Quantified a 16.7 pp SLA conversion gap (62.7% vs. 79.5%) using Chi-square statistical testing (p < 0.001).
> - Built Logistic Regression and Random Forest classifiers, achieving 0.8695 ROC-AUC with leakage-aware features.
> - Segmented 1,500 patients into 3 personas using K-Means on intent, engagement, response time, and case value.

---

# Tier 1: The 30–40 Second Elevator Pitch
**When to use:** *"Tell me about yourself"*, *"Walk me through a project on your resume"*, or initial Recruiter / HR / Hiring Manager screen (~95–110 words).

### Word-for-Word Script
> "At MedTourEasy, I built an end-to-end patient conversion and provider intelligence system across **1,500 international medical tourism inquiries** and **5 relational datasets** representing **INR 248.3M in completed treatment revenue** and **INR 111.5M in gross margin**.
>
> First, I engineered a Python and SQL data quality pipeline that uncovered **229 off-system treatment completions** that were inflating quote conversion from **57.9% to 98.8%**. Second, using Chi-square testing against country-specific SLA benchmarks, I proved that **82.8% of inquiries breached SLA**, causing a **16.7 percentage point drop in consultation booking** (`62.7%` vs. `79.5%`, $p < 0.001$).
>
> Finally, I built a **leakage-free Random Forest model achieving 0.8695 ROC-AUC** at a 72-hour prediction cutoff and combined it with **K-Means clustering (`k=3`)** to isolate **426 High-Value At-Risk patients** averaging **INR 716.8k per case**, creating a targeted routing playbook to recover an estimated **INR 7.5M in gross margin** at a 10% recovery rate."

### Delivery & Pacing Cues
- **0–10 sec (The Hook & Scale):** Emphasize `1,500 patient journeys`, `5 datasets`, and `INR 248.3M revenue / INR 111.5M gross margin`.
- **10–25 sec (Data Engineering + Statistical Proof):** Hit the `229 unquoted completions` anomaly and the `16.7 pp SLA conversion gap (62.7% vs. 79.5%, p < 0.001)`.
- **25–40 sec (ML + Segmentation + ROI):** Close with `0.8695 ROC-AUC` (72h leakage-free cutoff), `3 K-Means personas` (`426 High-Value At-Risk` patients), and `INR 7.5M gross margin` scenario.

---

# Tier 2: The 2–3 Minute Structured Technical Walkthrough
**When to use:** Technical Screen / Hiring Manager Deep-Dive (*"Walk me through your MedTourEasy project in detail"* — ~380–420 words). Structured directly around your 4 resume bullets.

### Word-for-Word Script

#### 1. Business Problem & Data Pipeline (Bullet 1 — ~45 seconds)
> "MedTourEasy coordinates cross-border medical travel across 12 source countries, 8 high-acuity specialties like Oncology and Cardiac Surgery, and 30 partner hospitals. Out of **1,500 patient inquiries**, **554 completed treatment** (`36.93%`), generating **INR 248.3M in revenue** and **INR 111.5M in gross margin** (`44.91%` margin rate). However, **946 patients failed to complete treatment**—including **350 explicitly coded drop-offs** representing **INR 166.5M in lost case-value exposure**.
>
> To diagnose this, I engineered a modular Python and SQLite pipeline across **5 datasets**: `patient_journey` (1,500 rows), `provider_master` (30 hospitals), `communication_logs` (6,025 interactions), `treatment_outcomes` (554 completed cases), and `country_reference` (12 countries). Because the legacy SQLite tables stored numeric fields as `TEXT` without primary or foreign key enforcement, I wrote explicit type-casting and reconciliation tests. That audit caught a critical funnel flaw: **229 out of 554 completed patients (`41.3%`) had `quote_shared = 0`**, which made naive quote-to-treatment conversion look like **98.75%** (`554 / 561`). Filtering to strict sequential progression (`325 / 561`) revealed the true **57.93%** quote conversion rate."

#### 2. Statistical SLA Breach Analysis (Bullet 2 — ~40 seconds)
> "Next, rather than using a single global response threshold, I joined every inquiry to its country-specific SLA benchmark (`6h`, `8h`, or `12h`). I found that **82.80% of inquiries (`1,242 / 1,500`) breached SLA**—with averages around `17 hours`.
>
> Running a Chi-square test of independence, I proved that patients whose response met SLA booked consultations at **79.46% (`205 / 258`)**, compared to **62.72% (`779 / 1,242`)** when SLA was breached—a **16.74 percentage point drop** ($\chi^2 = 25.78, p = 3.83 \times 10^{-7}$). I also confirmed this continuously with Welch's t-test: booked consultations averaged **15.77 hours** vs. **19.40 hours** for non-booked leads ($t = -7.96, p = 4.84 \times 10^{-15}$)."

#### 3. Leakage-Aware Machine Learning (Bullet 3 — ~45 seconds)
> "Third, to predict `treatment_completed` early enough for coordinators to intervene, I defined a strict **72-hour post-inquiry prediction cutoff**. I excluded all post-treatment financials, `satisfaction_score` (which is structurally null for all 946 non-completed patients), and downstream funnel flags (`consultation_booked`, `quote_shared`, `drop_off_flag`), and aggregated `communication_logs` strictly within $\le 72$ hours.
>
> Using a stratified 80/20 split (`1,200` train / `300` test) inside a `scikit-learn` `ColumnTransformer` pipeline, I compared balanced Logistic Regression (**0.8193 ROC-AUC**) against a regularized Random Forest (**0.8695 ROC-AUC**, **0.7723 Precision**, **0.7358 F1**). And because a missed patient costs **INR 201k in gross margin** while a coordinator call costs almost nothing, I tuned the probability threshold from `0.50` to `0.40`, boosting **Recall from 70.3% to 78.4%**."

#### 4. K-Means Patient Segmentation & Business Impact (Bullet 4 — ~40 seconds)
> "Finally, a risk score alone doesn't distinguish a low-intent lead from an expensive surgical case. I standardized `intent_score`, `engagement_score`, `response_time_hours`, and `estimated_case_value_inr` using `StandardScaler` and segmented patients via **K-Means (`k=3`)** into:
> 1. **High-Intent Converters** (`38.1%`, `60.2%` completion),
> 2. **High-Risk Disengaged** (`33.5%`, `14.7%` completion, slowest `19.8h` response), and
> 3. **High-Value At-Risk** (`28.4%`, `426` patients) who carry the highest average case value at **INR 716.8k** (2.2x other clusters) but convert at only **31.9%**.
>
> By routing `High-Value At-Risk` patients with ML probability between `0.35` and `0.65` to our top hospitals (`PVD-020`, `PVD-008`) and fastest coordinators (`COORD-06`), recovering just **10% of the 350 drop-offs** yields **INR 16.65M in revenue** and **INR 7.48M in gross margin**."

---

# Tier 3: The 10–15 Minute Deep-Dive Technical Defense
**When to use:** Final-round technical panel, case presentation, or architecture review.

## Minute 0:00 – 2:00 | Business Context, Unit Economics & Architecture
- **Business Model:** MedTourEasy is a global medical tourism facilitator connecting patients from **12 countries** (Bangladesh, India, Kenya, Malaysia, Nepal, Nigeria, Oman, Philippines, Sri Lanka, Tanzania, Thailand, UAE) across **7 acquisition channels** to **30 accredited partner hospitals (`PVD-001` to `PVD-030`)** and **10 coordinators (`COORD-01` to `COORD-10`)** across **8 treatment categories** (Cardiac Surgery, Cosmetic Surgery, Dental Care, Fertility Treatment, Neurology, Oncology, Organ Transplant, Orthopedic).
- **Verified Unit Economics:**
  - Total Inquiries: **1,500** | Completed Treatments: **554** (**36.93%** overall conversion)
  - Non-Completed Inquiries: **946** (**63.07%**), of which **350** (`23.33%`) are explicitly coded drop-offs (`drop_off_flag = 1`) and **596** (`39.73%`) remain open/stagnant in `Inquiry` (`212`), `Consultation` (`264`), or `Quote Shared` (`120`).
  - Completed Treatment Revenue: **INR 248,325,245** (`INR 248.33M`, mean **INR 448,241**/completed case)
  - Completed Service Cost: **INR 136,810,889** (`INR 136.81M`, mean **INR 246,951**/completed case)
  - Realized Gross Margin: **INR 111,514,356** (`INR 111.51M`, **44.91%** gross margin rate, mean **INR 201,289** margin/completed case)
- **End-to-End Repository Architecture:**
  - `src/data_quality.py` (PK/FK validation, SQLite-to-CSV reconciliation, missingness classification, funnel anomaly detection)
  - `src/analytics.py` (Dual-definition funnel, Chi-square & Welch's t-test SLA proofs, composite Provider Scorecard, channel/country economics, financial scenario table)
  - `src/modeling.py` (72-hour leakage-free feature engineering, `ColumnTransformer` + `Pipeline`, Logistic Regression & Random Forest, threshold sweep `0.30–0.70`)
  - `src/segmentation.py` (`StandardScaler` + K-Means evaluation $k \in \{2..6\}$, 3-persona assignment & economic profiling)
  - `sql/medtoureasy_analysis.sql` (11 analytical SQL queries with explicit `CAST`)
  - `dashboard/app.py` (6-page Streamlit executive command center) + `tests/test_pipeline.py` (11 automated `pytest` assertions).

---

## Minute 2:00 – 5:00 | Bullet 1 Defense: Python/SQL Pipeline, Data Quality & Provider Analytics
> *Resume Bullet 1: "Engineered Python/SQL pipeline across 1,500 patient journeys and 5 datasets for funnel and provider analytics."*

### 1. Schema & Relational Integrity Across 5 Datasets
| Dataset | Rows x Cols | Primary Key | Foreign Keys Validated | Key Engineering Nuance |
| :--- | :--- | :--- | :--- | :--- |
| `patient_journey` | `1,500 x 26` | `patient_id` | `assigned_provider_id`, `country` | Contains **946 structural nulls** in `satisfaction_score` & **1,150 nulls** in `drop_off_stage`/`reason_for_drop_off` |
| `provider_master` | `30 x 11` | `provider_id` | `country` | Hospital accreditation (`JCI`, `NABH`, `ISO`), bed capacity, SLA target, base cost index |
| `communication_logs` | `6,025 x 9` | `communication_id` | `patient_id`, `coordinator_id` | **1,413 structural nulls** in `response_delay_hours` whenever `responded = 0` (`23.45%` unresponded) |
| `treatment_outcomes` | `554 x 9` | `patient_id` | `patient_id`, `provider_id` | 1:1 exact match with `treatment_completed = 1` rows; zero financial discrepancy |
| `country_reference` | `12 x 6` | `country` | — | Defines `baseline_response_expectation_hours` (`6h`, `8h`, `12h`), visa complexity, travel readiness |

- **SQLite Type Hardening:** The SQLite database (`mte_patient_intelligence.db`) imported all columns as `TEXT` without `PRIMARY KEY` or `FOREIGN KEY` constraints. Every SQL query in `sql/medtoureasy_analysis.sql` applies explicit `CAST(col AS INTEGER)` and `CAST(col AS REAL)` so aggregations and numerical sorting never fail or sort lexicographically.

### 2. The "229 Unquoted Completions" Funnel Discovery
- **Raw Flag Counts:** `1,500` Inquiries (`100%`) $\rightarrow$ `984` Consultations Booked (`65.60%`) $\rightarrow$ `561` Quotes Shared (`37.40%` of inquiries, `57.01%` of consultations) $\rightarrow$ `554` Recorded Completions (`36.93%` of inquiries).
- **Why Naive Math Is Misleading:** Dividing `554` completed treatments by `561` quotes shared gives an artificial **98.75%** quote-to-treatment conversion rate.
- **Root Cause:** Auditing stage flags (`consultation_booked`, `quote_shared`, `treatment_completed`) revealed **229 completed patients (`41.34%` of all 554 completions) have `consultation_booked = 1` and `treatment_completed = 1` but `quote_shared = 0`** (direct hospital packages, corporate/insurance referrals, or coordinators skipping CRM quote logging).
- **Corrected Dual-Funnel Reporting:**
  1. **Strict Sequential Funnel (`Inquiry -> Consultation -> Quote -> Completion`):** `1,500` $\rightarrow$ `984` (`65.60%`) $\rightarrow$ `561` (`57.01%`) $\rightarrow$ `325` (**57.93%** true quote-to-treatment conversion; `21.67%` overall strict conversion).
  2. **Bypass / Unquoted Track:** `229` completions (`15.27%` of inquiries) completed without `quote_shared = 1`.
- **Primary Funnel Bottlenecks:** `516` inquiries lost before consultation (`34.40%` drop) and `423` consultations lost before quote sharing (`42.99%` drop).

### 3. Composite Provider Intelligence Scorecard
- Built a weighted **0–100 Provider Intelligence Score** across all 30 hospitals (averaging 50 assigned leads/provider, range 38–66, so sample sizes are statistically stable):
  $$\text{Score} = 0.30(\text{Norm Conv Rate}) + 0.20(\text{Norm SLA Adherence}) + 0.15(\text{Norm Follow-up}) + 0.15(\text{Norm Satisfaction}) + 0.20(\text{Norm Margin/Lead})$$
- **Top Providers:** `PVD-020` (Score **80.78**, `52.73%` conv, `5.85h` response, `72.73%` SLA adherence, `INR 85,172` margin/lead) and `PVD-008` (Score **71.77**, `48.21%` conv, highest margin/lead at **INR 111,739**).
- **Operational Diagnostic Power:** Exposes high-skill/low-SLA bottlenecks like `PVD-007` (`52.00%` conversion and `INR 110,602` margin/lead, but only **18.00% SLA adherence** at `10.17h` response) vs. chronic underperformers like `PVD-023` (`26.92%` conv, `0.00%` SLA adherence, `24.16h` response) and `PVD-002` (`23.08%` conv, `0.00%` SLA adherence).

---

## Minute 5:00 – 8:00 | Bullet 2 Defense: SLA Breach & Hypothesis Testing
> *Resume Bullet 2: "Quantified a 16.7 pp SLA conversion gap (62.7% vs. 79.5%) using Chi-square statistical testing (p < 0.001)."*

### 1. Country-Specific SLA Definition
- Joined `patient_journey.response_time_hours` against `country_reference.baseline_response_expectation_hours`:
  - **6-Hour SLA:** Nigeria, Nepal, Sri Lanka
  - **8-Hour SLA:** India, Malaysia, Philippines, Tanzania, UAE
  - **12-Hour SLA:** Bangladesh, Kenya, Oman, Thailand
- Defined $\text{sla\_breach} = \mathbb{I}(\text{response\_time\_hours} > \text{baseline\_response\_expectation\_hours})$.
- **System-Wide Finding:** **1,242 of 1,500 inquiries (`82.80%`) breached SLA**; only **258 (`17.20%`)** met SLA. Highest breach rates occur in **6-hour SLA countries** (`Nigeria 97.6%`, `Sri Lanka 97.2%`, `Nepal 94.7%`) because coordinator staffing operates on a uniform ~17-hour cycle regardless of origin market.

### 2. Primary Statistical Proof: Pearson's Chi-Square Test
- **2x2 Contingency Table (`sla_breach` vs. `consultation_booked`):**
  - **SLA Compliant (`n = 258`):** `205` booked (**79.46%**), `53` not booked (`20.54%`)
  - **SLA Breached (`n = 1,242`):** `779` booked (**62.72%**), `463` not booked (`37.28%`)
- **Absolute Conversion Penalty:** $62.72\% - 79.46\% = \mathbf{-16.74\text{ percentage points}}$ (95% Wald CI: **[-22.39 pp, -11.09 pp]**; Odds Ratio = **0.435**).
- **Test Statistics:** $\chi^2 = \mathbf{25.7784}$ (with Yates' continuity correction, $\text{dof} = 1$), $p = \mathbf{3.83 \times 10^{-7}}$ ($p < 0.001$), Cramér's $V = \mathbf{0.1311}$.
- **Downstream Ripple Effect:** SLA-compliant inquiries also achieve higher quote sharing (**46.90%** vs. **35.43%**, $+11.47\text{ pp}$) and higher treatment completion (**46.51%** vs. **34.94%**, $+11.57\text{ pp}$).

### 3. Complementary Continuous Proof: Welch's Two-Sample t-Test
- Because dichotomizing a continuous variable at a threshold can lose information, I also ran **Welch's t-test** (which does not assume equal variances across groups) on raw `response_time_hours`:
  - **Consultation Booked (`n = 984`):** Mean = **15.77h** ($\text{SD} = 7.91\text{h}$, Median = `15.45h`)
  - **Consultation Not Booked (`n = 516`):** Mean = **19.40h** ($\text{SD} = 8.63\text{h}$, Median = `19.40h`)
  - **Difference:** $\Delta = \mathbf{-3.63\text{ hours}}$, Welch's $t = \mathbf{-7.9569}$, $p = \mathbf{4.84 \times 10^{-15}}$, Cohen's $d = \mathbf{-0.431}$ (medium effect size).

### 4. Causal Inference Maturity: Association vs. Causation
- In observational CRM data, response time can be confounded by hospital capacity, time-of-day arrival, or coordinator workload. Therefore, I framed the 16.7 pp gap as a **statistically significant observational association** and designed a **stratified randomized controlled A/B test** (randomizing incoming leads within country x treatment strata to a `<4h` rapid-response desk vs. standard queue, needing ~340 leads/arm for 80% power at $\alpha = 0.05$).

---

## Minute 8:00 – 12:00 | Bullet 3 Defense: Leakage-Aware ML Pipeline (`0.8695 ROC-AUC`)
> *Resume Bullet 3: "Built Logistic Regression and Random Forest classifiers, achieving 0.8695 ROC-AUC with leakage-aware features."*

### 1. Defining the Prediction Point & Preventing Target Leakage
- **Business Goal:** Score every incoming inquiry at **72 hours post-inquiry** so operations can intervene *before* the patient drops off.
- **Three Categories of Leakage Removed:**
  1. **Post-Treatment Financials & Outcomes:** Excluded `actual_revenue_inr`, `service_cost_inr`, `gross_margin_inr`, and all `treatment_outcomes` fields (`complication_flag`, `length_of_stay_days`).
  2. **Structural Null Proxy (`satisfaction_score`):** `satisfaction_score` is populated *only* for the 554 completed cases (`0%` missing when `treatment_completed = 1`, `100%` missing when `treatment_completed = 0`). Including it with median imputation lets a tree split on `is_imputed` and achieve ~100% fake accuracy. Excluded completely.
  3. **Downstream Funnel Flags & Future Logs:** Excluded `consultation_booked`, `quote_shared`, `follow_up_completed`, `current_stage`, `drop_off_flag`, `drop_off_stage`, and `reason_for_drop_off`. Filtered `communication_logs` strictly to $0 \le t_{\text{comm}} - t_{\text{inquiry}} \le 72\text{ hours}$ (`early_interactions`, `early_response_rate`, `early_avg_response_delay`, `early_followup_completed`).

### 2. Preprocessing & Model Comparison (Stratified 80/20 Split: `1,200` Train / `300` Test)
- Built a unified `scikit-learn` `Pipeline` + `ColumnTransformer` (`SimpleImputer(strategy="median")` + `StandardScaler()` on 19 numeric features; `SimpleImputer(strategy="most_frequent")` + `OneHotEncoder(handle_unknown="ignore")` on 6 categorical features) so all statistics are fit **strictly on the 1,200 training rows**.

| Model | ROC-AUC | Accuracy | Precision | Recall | F1-Score | Confusion Matrix (`TN, FP, FN, TP`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression** (`class_weight="balanced"`) | `0.8193` | `0.7400` | `0.6187` | `0.7748` | `0.6880` | `TN=136, FP=53, FN=25, TP=86` |
| **Random Forest** (`n_estimators=500, min_samples_leaf=3, max_features=0.7, class_weight="balanced"`) | **0.8695** | **0.8133** | **0.7723** | `0.7027` | **0.7358** | `TN=166, FP=23, FN=33, TP=78` |

- **Why Random Forest Outperformed (+0.0502 ROC-AUC):** Conversion probability exhibits strong non-linear threshold interactions (e.g., `engagement_score x response_time_hours` and `estimated_case_value_inr x medical_complexity_index`).
- **Top 5 Predictive Drivers (Random Forest Gini Importance):**
  1. `engagement_score`: **29.63%** (Logistic OR = `3.15` per +1 SD)
  2. `estimated_case_value_inr`: **12.96%** (Logistic OR = `0.63` — higher-cost cases face steeper price shock)
  3. `intent_score`: **7.53%** (Logistic OR = `1.63` per +1 SD)
  4. `response_time_hours`: **7.42%** (Logistic OR = `0.70` per +1 SD)
  5. `early_avg_response_delay` (0–72h): **4.70%**

### 3. Cost-Sensitive Threshold Tuning
- **Asymmetric Cost Ratio:** A **False Negative (FN)** risks losing a salvageable patient worth **INR 201,289 in gross margin**, whereas a **False Positive (FP)** costs 15 minutes of coordinator follow-up (~INR 500).
- Lowering the classification threshold from **0.50 to 0.40** increases **Recall from 70.27% to 78.38%** (+8.11 pp, catching 9 additional completers in the 300-patient test set) while maintaining **67.97% Precision** and **0.7280 F1**.

---

## Minute 12:00 – 15:00 | Bullet 4 Defense: K-Means Personas & Financial ROI
> *Resume Bullet 4: "Segmented 1,500 patients into 3 personas using K-Means on intent, engagement, response time, and case value."*

### 1. Clustering Design & Validation
- **Feature Selection:** `intent_score` (0–100), `engagement_score` (0–100), `response_time_hours` (1–46h), `estimated_case_value_inr` (INR 75k–1.5M).
- **Why `StandardScaler` Is Mandatory:** Without z-score standardization ($\mu=0, \sigma=1$), `estimated_case_value_inr` (measured in hundreds of thousands of rupees) accounts for $>99.99\%$ of raw Euclidean distance.
- **Choosing $k=3$:** Evaluated $k \in \{2..6\}$ via Inertia, Silhouette Score, and Davies-Bouldin Index (`k=2` Sil `0.264`, `k=3` Sil `0.233` / DBI `1.448`, `k=4` Sil `0.219`). While $k=2$ merely splits high vs. low engagement, **$k=3$ isolates the critical high-value surgical segment** that requires senior clinical escalation.

### 2. The 3 Actionable Patient Personas
| Persona Name | Size | Mean Intent | Mean Engagement | Mean Resp Time | Mean Case Value | Consult Rate | Completion Rate | Drop-Off Rate | Realized Gross Margin |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **High-Intent Converters** (Cluster 1) | `571` (`38.1%`) | `75.3` | `69.7` | `15.0h` | `INR 327.0k` | **82.0%** | **60.2%** | `10.2%` | **INR 52.20M** |
| **High-Value At-Risk** (Cluster 2) | `426` (`28.4%`) | `63.1` | `55.5` | `16.4h` | **INR 716.8k** | `67.8%` | `31.9%` | `24.6%` | **INR 46.58M** |
| **High-Risk Disengaged** (Cluster 0) | `503` (`33.5%`) | `45.6` | `32.1` | **19.8h** | `INR 402.1k` | `45.1%` | `14.7%` | **37.2%** | **INR 12.74M** |

### 3. Operational Playbook & Scenario-Based Financial Impact
- **2x2 Triage Matrix (Persona x ML Probability):**
  - **Tier 1 Escalation (`High-Value At-Risk` + ML Prob `0.35–0.65`):** Route immediately to top-scoring hospitals (`PVD-020`, `PVD-008`) and senior coordinators (`COORD-06`, `COORD-03`) with transparent itemized surgical quotes and tele-consults.
  - **Fast-Track Automation (`High-Intent Converters`):** Automated travel/visa checklists (`59.1%` of this segment is already travel-ready) to free coordinator capacity.
  - **Low-Cost Nurture (`High-Risk Disengaged`):** Automated `<1h` WhatsApp/Chatbot intake before assigning human coordinator hours.
- **Audited Financial Scenarios (350 Coded Drop-Offs = INR 166.51M Case-Value Exposure):**
  - **5% Recovery (Conservative — ~18 cases):** **INR 8.33M** incremental revenue | **INR 3.74M** gross margin (at observed `44.91%` margin rate).
  - **10% Recovery (Base Target — ~35 cases):** **INR 16.65M** incremental revenue | **INR 7.48M** gross margin.
  - **15% Recovery (Stretch — ~53 cases):** **INR 24.98M** incremental revenue | **INR 11.22M** gross margin.
  - **20% Recovery (Best-In-Class — ~70 cases):** **INR 33.30M** incremental revenue | **INR 14.96M** gross margin.

---

# Bullet-by-Bullet "Interviewer Cross-Examination" Cheat Sheet

### Bullet 1 Cross-Examination
1. **"What was the nastiest data quality bug you found across the 5 datasets?"**
   - *Answer:* Two stood out: (1) **229 completed patients (`41.3%` of 554 completions) had `quote_shared = 0`**, which inflated naive quote-to-treatment conversion to `98.75%` instead of the true sequential `57.93%`; and (2) **structural missingness** in `satisfaction_score` (`946/1,500` missing = exact non-completed rows) and `response_delay_hours` (`1,413/6,025` missing = exact unresponded logs), which would cause severe target leakage or bias if blindly imputed.
2. **"Why didn't you rank providers purely by conversion rate?"**
   - *Answer:* Conversion rate alone ignores unit economics and SLA discipline. For example, `PVD-007` had a `52.0%` conversion rate but only `18.0%` SLA adherence, whereas `PVD-020` balanced `52.7%` conversion with `72.7%` SLA adherence (`5.85h` avg response). Our 5-factor composite score weights Conversion (`30%`), SLA Adherence (`20%`), Margin/Lead (`20%`), Follow-up (`15%`), and Satisfaction (`15%`).

### Bullet 2 Cross-Examination
1. **"Why did you use both Chi-square and Welch's t-test for the SLA analysis?"**
   - *Answer:* Chi-square tests the operational binary SLA rule (`sla_breach` vs. `consultation_booked`, giving the `-16.74 pp` gap, $\chi^2 = 25.78, p = 3.83 \times 10^{-7}$). However, binary cutoffs discard continuous variation, so I paired it with Welch's t-test on raw `response_time_hours` (`15.77h` vs. `19.40h`, $t = -7.96, p = 4.84 \times 10^{-15}$) to prove the relationship holds both at the SLA boundary and continuously.
2. **"Can you claim that reducing response time *causes* a 16.7 pp lift?"**
   - *Answer:* No—observational CRM data has confounders (e.g., complex oncology inquiries may take longer to review and also convert differently). That is why I stated it as an observational association and proposed a stratified randomized A/B test on `<4h` routing.

### Bullet 3 Cross-Examination
1. **"How exactly did you prevent data leakage in your 0.8695 ROC-AUC model?"**
   - *Answer:* I enforced a **72-hour post-inquiry cutoff**: dropped post-treatment columns (`actual_revenue_inr`, `service_cost_inr`, `gross_margin_inr`, `satisfaction_score`), dropped downstream stage flags (`consultation_booked`, `quote_shared`, `drop_off_flag`), filtered `communication_logs` to $\le 72\text{h}$ post-inquiry, and wrapped all imputation/scaling inside a `scikit-learn` `ColumnTransformer` fit strictly on `X_train`.
2. **"Why did you deploy both Logistic Regression and Random Forest?"**
   - *Answer:* Logistic Regression (`0.8193` ROC-AUC) gives calibrated directional **Odds Ratios** for executives (`engagement_score` OR = `3.15`, `response_time_hours` OR = `0.70`), while Random Forest (`0.8695` ROC-AUC) captures non-linear interactions (`engagement x response time` and `case value x complexity`) for superior ranking accuracy.

### Bullet 4 Cross-Examination
1. **"The Silhouette score at k=3 is 0.233—isn't that low?"**
   - *Answer:* In continuous behavioral CRM data (`intent`, `engagement`, `response_time`, `case_value`), patients form a continuous manifold rather than isolated spheres, so Silhouette scores between `0.22` and `0.28` are standard. While $k=2$ had a slightly higher Silhouette (`0.264`), it merged high-value surgical patients into general segments. $k=3$ isolated the **426 High-Value At-Risk** patients (`INR 716.8k` avg case value, `31.9%` conversion), which is the highest-ROI operational discovery in the dataset.
