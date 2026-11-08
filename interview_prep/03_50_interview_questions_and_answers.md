# 50 Project-Specific Interview Questions, Answers & Follow-Up Defenses

This bank covers **50 project-specific interview questions** across Data Engineering, Funnel & Product Analytics, Statistical Testing, Provider/Channel Strategy, Supervised ML, Unsupervised Clustering, SQL, and Executive Business Impact, followed by common interviewer follow-up traps.

---

## Part A: Data Engineering, Schema Governance & Reconciliation (Q1–Q8)

### Q1. What tables make up the MedTourEasy dataset and how do their primary and foreign keys relate?
**Answer:** There are 5 relational tables:
1. `patient_journey` (`1,500` rows, PK: `patient_id`) — core inquiry-to-treatment funnel table.
2. `provider_master` (`30` rows, PK: `provider_id`) — hospital metadata and historical benchmarks.
3. `communication_logs` (`6,025` rows, PK: `communication_id`) — timestamped touchpoints linked via `patient_id` and `provider_id`.
4. `treatment_outcomes` (`554` rows, PK: `patient_id`) — post-treatment clinical and financial outcomes linked 1:1 to completed patients and `provider_id`.
5. `country_reference` (`12` rows, PK: `country`) — market-level SLA expectations and priority scores linked via `country`.
All 5 primary keys have `0` nulls and `0` duplicates, and all 6 foreign-key relationships have `0` orphan records.

### Q2. What schema vulnerabilities did you uncover in `mte_patient_intelligence.db`?
**Answer:** First, every column across all 5 SQLite tables was declared as `TEXT`, meaning numeric fields (`actual_revenue_inr`, `response_time_hours`) and dates (`inquiry_date`, `timestamp`) had no type enforcement at the storage layer. Second, `PRAGMA foreign_keys` was `0`, and no primary-key or foreign-key constraints or indexes were declared. In our SQL layer (`sql/medtoureasy_analysis.sql`), we explicitly cast every numeric field (`CAST(... AS INTEGER/REAL)`) and recommended a hardened DDL migration with typed columns, constraints, and B-tree indexes on `patient_id`, `provider_id`, and `country`.

### Q3. Why wasn't the column-level string match between CSV and SQLite 100% on floating-point columns like `intent_score` (98.27%) or `engagement_score` (96.27%)?
**Answer:** When pandas reads CSV floats, values like `5.0` are formatted as `"5.0"`, whereas SQLite `TEXT` storage preserves the raw string `"5"` (or vice versa for trailing zeros). Numerically, 100% of non-null values match to machine precision (`np.isclose`), and our reconciliation audit (`csv_sqlite_reconciliation.csv`) explicitly tracks normalized string representation differences alongside exact row-count parity.

### Q4. How did you prove that `satisfaction_score` missingness (63.1%) is structural rather than random?
**Answer:** Exactly `946` of the `1,500` rows in `patient_journey` have a null `satisfaction_score`. When cross-tabulated against `treatment_completed`, all `554` completed patients (`treatment_completed = 1`) have a valid satisfaction score, and all `946` non-completed patients (`treatment_completed = 0`) have `NULL`. Thus, satisfaction is only collected after treatment completion.

### Q5. How did you handle the 1,413 missing values (23.5%) in `communication_logs.response_delay_hours`?
**Answer:** We verified that 100% of the `1,413` rows with null `response_delay_hours` have `response_sent = 0`. A null delay means no response was ever sent—not that the delay was `0` hours. In SQL and Python aggregations, we kept unanswered delays as `NULL` so `AVG(response_delay_hours)` measures the average turnaround time of *answered* messages, while `AVG(response_sent)` (`early_response_rate`) captures the proportion of messages answered.

### Q6. How did you reconcile financial figures between `patient_journey` and `treatment_outcomes`?
**Answer:** We ran a 6-point reconciliation (`financial_reconciliation.csv`):
1. Completed count: `554` in `patient_journey` (`treatment_completed=1`) vs. `554` rows in `treatment_outcomes`.
2. Total revenue: `₹248,325,245` in both tables.
3. Total service cost: `₹136,810,889` in both tables.
4. Gross margin: `₹111,514,356` in both tables, and `actual_revenue_inr - service_cost_inr == gross_margin_inr` holds for all 554 rows.
5. Completed cases with non-zero revenue: `554 / 554`.
6. Incomplete cases (`treatment_completed=0`) with non-zero revenue: `0 / 946`.

### Q7. Did any treatment dates occur before the patient's inquiry date?
**Answer:** No. Merging `treatment_outcomes.treatment_date` against `patient_journey.inquiry_date` confirmed `0` chronological inversions (`treatment_date >= inquiry_date` for all 554 completed cases).

### Q8. Why does `.gitignore` exclude the raw CSV and SQLite files from the public GitHub repository?
**Answer:** Even in synthetic or anonymized healthcare operations projects, committing raw patient-level (`patient_id`) records to a public repository violates healthcare data governance best practices (HIPAA / GDPR / DISHA principles). Keeping raw files local while committing reproducible code (`src/`, `scripts/`, `sql/`), aggregated outputs (`outputs/`), and automated tests (`tests/`) reflects production data engineering standards.

---

## Part B: Patient Funnel & Conversion Analytics (Q9–Q15)

### Q9. Walk me through the MedTourEasy patient funnel numbers from inquiry to completion.
**Answer:**
- **Total Inquiries:** `1,500` (100.0%)
- **Consultations Booked:** `984` (`65.60%` of inquiries)
- **Quotes Shared:** `561` (`57.01%` of consultations; `37.40%` of inquiries)
- **Recorded Treatment Completions:** `554` (`36.93%` of inquiries)
- **Strict Sequential Completions (with `quote_shared = 1`):** `325` (`57.93%` of quotes shared)

### Q10. What is the "229 unquoted completions" anomaly and why is it critical for funnel reporting?
**Answer:** Out of `554` patients with `treatment_completed = 1`, `229` have `quote_shared = 0`. If an analyst naively divides `554` completed treatments by `561` shared quotes, they get `98.75%` and falsely conclude that quote-to-treatment conversion has almost zero friction. In reality, `229` patients bypassed quote flag logging in the CRM (e.g., offline hospital quotes or direct admissions). Among the `561` patients with a recorded quote flag, `325` completed treatment—a true sequential quote-to-treatment conversion rate of **`57.93%`**.

### Q11. Where is the largest absolute volume drop-off in the funnel?
**Answer:** In raw stage progression, the largest absolute drop is **Inquiry to Consultation**, where **`516` patients (`34.4%` of all inquiries)** fail to book a consultation. The second-largest stage drop is **Consultation to Quote Shared**, where **`423` booked consultations (`43.0%` of consultations)** never receive a recorded quote.

### Q12. Why are there 350 explicitly coded drop-offs (`drop_off_flag = 1`) when 946 patients did not complete treatment?
**Answer:** In CRM operations, `drop_off_flag = 1` (`350` cases) represents patients who were *explicitly closed-lost* with a documented `drop_off_stage` and `reason_for_drop_off`, whereas the remaining `596` non-completed patients (`946 - 350`) are unclosed/stalled leads remaining in intermediate funnel stages (`First Response`, `Consultation`, `Quote Shared`) without a formal closed-lost reason code. Our analysis tracks both stage-based non-conversion (`946` total, `516` pre-consultation) and explicitly coded drop-offs (`350`).

### Q13. Which funnel stages account for the 350 explicitly coded drop-offs?
**Answer:**
1. **Inquiry:** `103` cases (`29.43%`)
2. **First Response:** `89` cases (`25.43%`)
3. **Consultation:** `55` cases (`15.71%`)
4. **Treatment Plan:** `49` cases (`14.00%`)
5. **Quote Shared:** `43` cases (`12.29%`)
6. **Travel Planning:** `11` cases (`3.14%`)
Notably, **`54.86%` (`192 / 350`)** of coded drop-offs happen at the `Inquiry` and `First Response` stages before a consultation even takes place.

### Q14. What are the top reasons for patient drop-off?
**Answer:** Among the 350 coded drop-offs, the top three operational reasons are **No follow-up (`66` cases)**, **Cost concern (`62` cases)**, and **Response delay (`60` cases)**—meaning **`126 / 350` (`36.0%`)** of coded drop-offs are directly tied to controllable coordinator/provider responsiveness (`No follow-up` + `Response delay`).

### Q15. How do conversion rates evolve across monthly inquiry cohorts (`Q8` in SQL)?
**Answer:** Monthly cohort analysis across the 12 months of 2025 (`2025-01` through `2025-12`) shows stable inquiry volumes (~`115–135` inquiries/month) and consistent consultation (`~62%–70%`) and completion (`~33%–41%`) rates, confirming that funnel leakage is a systemic operational process issue rather than a single-month seasonal spike.

---

## Part C: Statistical Hypothesis Testing & SLA Analysis (Q16–Q22)

### Q16. How is an SLA breach defined in this project?
**Answer:** Each patient's `country` is joined to `country_reference.baseline_response_expectation_hours` (`6`, `8`, or `12` hours). A patient journey is flagged as `sla_breach = True` if `response_time_hours > baseline_response_expectation_hours`. Across all 1,500 patients, **`1,242` (`82.80%`)** breached their country SLA, and **`258` (`17.20%`)** met SLA.

### Q17. What were the exact results of the Chi-square test between SLA breach and consultation booking?
**Answer:**
- **SLA Compliant (`n = 258`):** `205` booked a consultation (**`79.46%`**).
- **SLA Breached (`n = 1,242`):** `779` booked a consultation (**`62.72%`**).
- **Absolute Gap:** **`-16.74` percentage points** (95% CI: `[-22.39 pp, -11.09 pp]`).
- **Chi-Square Statistic:** $\chi^2 = 25.7784$ ($\text{dof}=1$, with Yates' continuity correction), **$p = 3.83 \times 10^{-7}$**, Cramér's $V = 0.1311$.

### Q18. What were the exact results of Welch's $t$-test on response time?
**Answer:**
- **Booked Consultations (`n = 984`):** Mean response time = **`15.77 hours`** (`15.7655h`).
- **Not Booked (`n = 516`):** Mean response time = **`19.40 hours`** (`19.3998h`).
- **Mean Difference:** **`-3.63 hours`** (95% CI: `[-4.53h, -2.74h]`).
- **Welch's $t$-statistic:** $t = -7.9569$, **$p = 4.84 \times 10^{-15}$**, Cohen's $d = -0.431$.

### Q19. Why did you use Welch's $t$-test instead of Student's $t$-test or Mann-Whitney U?
**Answer:** Welch's $t$-test (`scipy.stats.ttest_ind(..., equal_var=False)`) does not assume equal variances across groups and adjusts degrees of freedom via the Welch–Satterthwaite formula, which is critical when sample sizes are unequal (`984` vs. `516`). With $N = 1,500$, the Central Limit Theorem guarantees that sample means are normally distributed even if individual response times are modestly skewed, and parametric mean differences (`hours`) are directly interpretable by operations managers.

### Q20. Which source countries have the highest SLA breach rates, and why?
**Answer:** The highest SLA breach rates occur in the **6-hour baseline SLA markets**: **Sri Lanka (`93.97%` breach)**, **Nigeria (`93.16%` breach, lowest completion rate at `28.21%`)**, and **Nepal (`90.23%` breach)**, followed by 8-hour market **Philippines (`91.49%` breach)**. Because coordinator response times average `16–18 hours` globally regardless of market, countries requiring a `6-hour` turnaround suffer >90% breach rates.

### Q21. Can we conclude from $p = 3.83 \times 10^{-7}$ that reducing response times will causally increase consultation bookings by 16.7 percentage points?
**Answer:** No. $p < 0.001$ rules out random chance in observational association, but it does not eliminate confounding bias. For example, patients inquiring during daytime hours with complete medical records might both receive faster coordinator replies and have higher intrinsic booking intent. To estimate the causal treatment effect, we must run a randomized controlled trial (A/B test) on incoming lead routing.

### Q22. How would you design an A/B test to validate the causal impact of SLA adherence?
**Answer:**
- **Unit of Randomization:** Incoming patient inquiry (`patient_id`), stratified by `country` (6h/8h/12h SLA tier) and `lead_source`.
- **Treatment Group (50%):** Routed to an automated instant-triage + dedicated rapid-response coordinator pod with a hard `<4 hour` first-response SLA.
- **Control Group (50%):** Standard coordinator assignment queue.
- **Primary Success Metric:** 7-day `consultation_booked` conversion rate.
- **Guardrail Metrics:** Quote-to-treatment conversion rate and coordinator utilization/burnout.
- **Sample Size / Power:** To detect a conservative `+8 percentage point` lift from `65.6%` to `73.6%` at $\alpha = 0.05$ and $80\%$ power, we need approximately `515` inquiries per arm (`~1,030` total inquiries, or ~8–9 months of traffic across all channels, or 4 months if using covariate adjustment via CUPED with `intent_score`).

---

## Part D: Provider, Coordinator & Channel Intelligence (Q23–Q29)

### Q23. How did you construct the Composite Provider Intelligence Score?
**Answer:** Per the PRD and Assumptions Log, we combined five operational dimensions into a weighted `0–100` score:
- **30% Conversion Score:** Min-max normalized `conversion_rate` across the 30 providers (`23.08%` $\rightarrow 0$, `52.73%` $\rightarrow 100`).
- **20% SLA Adherence Score:** `sla_adherence_rate * 100`.
- **15% Follow-up Completion Score:** `follow_up_completion_rate * 100`.
- **15% Satisfaction Score:** `avg_satisfaction_score * 10` (scaling the 0–10 rating to 0–100).
- **20% Margin per Lead Score:** Min-max normalized `margin_per_lead` (`₹35,606` $\rightarrow 0$, `₹111,739` $\rightarrow 100$).

### Q24. Why is a composite score better than ranking providers purely by conversion rate?
**Answer:** Look at **`PVD-007`** vs. **`PVD-020`**: both have ~`52%` treatment conversion (`52.00%` vs `52.73%`), but `PVD-020` has a **`5.85h` average response time (`72.7%` SLA adherence)** and `38.2%` follow-up completion, whereas `PVD-007` has a **`15.41h` response time (`18.0%` SLA adherence, `82.0%` breach rate)**. Ranking on conversion alone would mask `PVD-007`'s severe intake SLA failures. The composite score places `PVD-020` at #1 (`80.78`), `PVD-008` at #2 (`71.77`), and `PVD-007` at #3 (`67.00`).

### Q25. Which providers are the top benchmarks and which are the bottom underperformers?
**Answer:**
- **Top 3 Benchmarks:** `PVD-020` (Score `80.78`, `52.7%` conv, `5.85h` response), `PVD-008` (Score `71.77`, `50.9%` conv, #1 margin/lead at `₹111,739`), and `PVD-007` (Score `67.00`, `52.0%` conv).
- **Bottom 3 Underperformers:** `PVD-023` (Rank 30, Score `13.06`, `23.9%` conv, `0%` SLA adherence, `₹35.6k` margin/lead), `PVD-013` (Rank 29, Score `16.02`, `24.0%` conv, `0%` SLA adherence), and `PVD-014` (Rank 28, Score `16.89`, `23.1%` conv, `9.6%` SLA adherence).

### Q26. Did you check sample sizes before ranking providers and coordinators?
**Answer:** Yes. Across the 30 partner hospitals, assigned lead volume is well-balanced between **`38` and `66` leads per provider** (mean `50.0` leads). Across the 15 coordinators, lead volume ranges from **`82` to `112` leads per coordinator** (mean `100.0` leads). In our Streamlit dashboard, we also added an interactive minimum-lead filter so leadership can verify rankings under stricter sample-size cutoffs.

### Q27. What did the Coordinator SLA analysis reveal?
**Answer:** All 15 coordinators currently struggle with country SLA baselines (breach rates range from `76.8%` for `COORD-12` to `88.0%` for `COORD-10`), proving that SLA breaches are a **systemic routing/staffing issue** rather than a single rogue employee. However, conversion performance varies substantially: `COORD-06` achieves **`42.34%` treatment completion** (`80 / 111` consultations booked), whereas `COORD-09` achieves only **`30.68%` completion** (`18.34h` avg response time).

### Q28. How do the 6 acquisition channels compare on conversion vs. unit economics?
**Answer:**
- **Phone (`244` leads):** Highest gross margin per lead (**`₹82,420`**), `67.6%` consultation rate, `38.5%` completion rate.
- **Email (`238` leads):** Highest completion rate (**`39.92%`**), lowest coded drop-off rate (**`18.91%`**), and #2 margin per lead (**`₹81,826`**), despite a lower initial consultation rate (`61.8%`).
- **WhatsApp (`272` leads):** Highest volume and highest total gross margin (**`₹21.02M`**), `69.1%` consultation rate, `38.6%` completion.
- **Chatbot (`254` leads):** Highest consultation booking rate (**`70.08%`**), `36.6%` completion, `₹75,779` margin/lead.
- **Referral Partner (`246` leads) & Web Form (`246` leads):** Lowest completion rates (`33.33%` and `34.55%`) and lowest margin per lead (`₹64,706` and `₹63,998`). `Web Form` has the highest coded drop-off rate (**`27.24%`**).

### Q29. Which treatment categories drive MedTourEasy's profitability?
**Answer:**
- **By Total Gross Margin & Margin per Case:** **Transplant Evaluation** (`₹22.24M` total margin, **`₹411,902` margin per completed case**), **Oncology** (`₹21.77M` total margin, **`₹298,278` margin/case**), and **Neurology** (`₹16.26M` total margin, **`₹232,247` margin/case**). Together, these three high-acuity specialties generate **`₹60.27M` (`54.0%`)** of MedTourEasy's entire gross margin!
- **By Completion Rate:** **Bariatric Surgery (`41.36%`)**, **Neurology (`40.23%`)**, and **Oncology (`39.04%`)** convert best, whereas **Fertility (`32.53%`)** and **Transplant Evaluation (`33.54%`)** have the lowest completion rates due to clinical/travel complexity.

---

## Part E: Machine Learning & Data Leakage Prevention (Q30–Q39)

### Q30. What is the exact prediction task and target variable in your ML pipeline?
**Answer:** Binary classification predicting **`treatment_completed` $\in \{0, 1\}$** at **72 hours post-inquiry**, evaluated on a fixed **80/20 stratified train-test split** (`1,200` train / `300` test rows, `random_state=42`, positive class prevalence `36.93%`).

### Q31. How did you prevent data leakage in feature engineering and preprocessing?
**Answer:** We applied three layers of leakage defense:
1. **Feature Selection Guardrail:** Explicitly excluded all post-treatment variables (`actual_revenue_inr`, `service_cost_inr`, `satisfaction_score`, `treatment_outcomes` fields) and downstream funnel flags (`consultation_booked`, `quote_shared`, `follow_up_completed`, `current_stage`, `drop_off_flag`, `drop_off_stage`, `reason_for_drop_off`). We even added an automated check in `train_and_evaluate_models()` that raises a `ValueError` if any forbidden feature is passed.
2. **Temporal Cutoff on Logs:** Filtered `communication_logs` strictly to $0 \le \text{timestamp} - \text{inquiry\_date} \le 72\text{ hours}$ before aggregating patient-level interaction counts, response rates, and response delays.
3. **Pipeline Encapsulation:** Wrapped `SimpleImputer`, `StandardScaler`, and `OneHotEncoder` inside a `scikit-learn` `ColumnTransformer` + `Pipeline` so imputation medians and scaling parameters are computed strictly on `X_train` and applied to `X_test`.

### Q32. Why did you include provider historical rates (`historical_consultation_conversion_rate`, etc.) in the ML model? Doesn't that leak the target?
**Answer:** No—those fields come from `provider_master.csv`, which represents the partner hospital's *historical baseline performance prior to the current cohort* (confirmed by the fact that `provider_master.historical_treatment_conversion_rate` averages `~0.07–0.38`, distinct from the current cohort's realized provider conversion rate). In production, knowing which hospital a patient was assigned to and that hospital's historical baseline is known at inquiry time ($t = 0$).

### Q33. Compare the test-set performance of Logistic Regression and Random Forest.
**Answer:**
- **Logistic Regression:** `ROC-AUC = 0.8193`, `Precision = 0.6187`, `Recall = 0.7748`, `F1 = 0.6880` (`TN=136, FP=53, FN=25, TP=86`).
- **Random Forest:** `ROC-AUC = 0.8695`, `Precision = 0.7723`, `Recall = 0.7027`, `F1 = 0.7358` (`TN=166, FP=23, FN=33, TP=78`).
Random Forest improves ROC-AUC by **+0.0502** and reduces False Positives by more than half (`23` vs `53`), achieving a **+0.0478 higher F1-score**.

### Q34. Why did Random Forest outperform Logistic Regression on this dataset?
**Answer:** Patient conversion depends on non-linear interactions between behavioral engagement, case value, specialty, and response time. For example, a high `estimated_case_value_inr` in `Transplant Evaluation` or `Oncology` has very different conversion dynamics depending on whether `engagement_score` is above `60` and `response_time_hours` is below `12h`. Decision trees naturally partition these interaction regions, whereas a linear Logistic Regression without manual interaction terms only models additive main effects in log-odds space.

### Q35. What are the top 5 most important features in the Random Forest model?
**Answer:**
1. `engagement_score` (**`29.63%`**)
2. `estimated_case_value_inr` (**`12.96%`**)
3. `intent_score` (**`7.53%`**)
4. `response_time_hours` (**`7.42%`**)
5. `early_avg_response_delay` (**`4.70%`**)
Together, these top 5 features account for **`62.24%`** of total Gini importance, and all 5 are directly actionable or observable within 72 hours of inquiry.

### Q36. Why didn't you optimize the models purely for classification accuracy?
**Answer:** With a `63.07% / 36.93%` class split, accuracy is insensitive to minority-class trade-offs and treats False Positives and False Negatives as equally costly. We used **ROC-AUC** to evaluate threshold-independent ranking quality and **Precision / Recall / F1** across thresholds (`0.30, 0.40, 0.50, 0.60`) to align the decision boundary with coordinator capacity and unit economics.

### Q37. Which probability threshold do you recommend for deployment and why?
**Answer:** We recommend **`threshold = 0.40`** for the Random Forest model. Compared to the default `0.50` threshold, lowering the threshold to `0.40` increases **Recall from `70.27%` (`78/111`) to `78.38%` (`87/111`)** while keeping **Precision at `67.97%`** (`F1 = 0.7280`). Missing a convertible international patient forfeits ~`₹201k` in gross margin, whereas reviewing 18 additional false positives (`41` FP vs `23` FP out of 300 patients) requires negligible coordinator effort.

### Q38. How did you handle class imbalance in both models?
**Answer:** First, we used `stratify=y` in `train_test_split` so both train (`1,200`) and test (`300`) sets preserve the exact `36.93%` positive class ratio (`111 / 300` positives in test). Second, we set `class_weight="balanced"` in both `LogisticRegression` and `RandomForestClassifier`, which weights each class inversely proportional to its frequency ($w_j = N / (2 \cdot N_j)$). Third, we tuned the classification probability threshold post-training.

### Q39. What is a limitation of Gini impurity feature importance in Random Forests, and how did you cross-check it?
**Answer:** Gini importance (mean decrease in impurity) can inflate the importance of continuous features with high cardinality (such as `estimated_case_value_inr`, which has 1,498 unique values) over binary one-hot encoded features. We cross-checked Random Forest importances against standardized **Logistic Regression coefficients / odds ratios**, confirming that `engagement_score`, `intent_score`, `response_time_hours`, and `early_avg_response_delay` remain the dominant drivers in both models.

---

## Part F: Patient Segmentation & K-Means Personas (Q40–Q44)

### Q40. Which features were used for K-Means segmentation and why?
**Answer:** We used four continuous pre-treatment variables:
1. `intent_score` (initial clinical readiness)
2. `engagement_score` (responsiveness & interaction depth)
3. `response_time_hours` (service speed experienced by the patient)
4. `estimated_case_value_inr` (economic value & procedure complexity)
These four dimensions capture patient readiness, operational speed, and financial value without leaking outcome labels (`treatment_completed` or `drop_off_flag`), which are reserved for post-clustering validation!

### Q41. How did you evaluate cluster quality and choose $k = 3$?
**Answer:** We standardized the 4 features with `StandardScaler` and evaluated $k \in \{2, 3, 4, 5, 6\}$ using **Within-Cluster Sum of Squares (Inertia / Elbow method)**, **Silhouette Score**, and **Davies-Bouldin Index**. At $k = 3$, the clusters separate cleanly along both the behavioral axis (High vs. Low Engagement/Intent) and the economic axis (Standard vs. High Case Value), creating three personas that map directly to distinct coordinator workflows.

### Q42. Describe the three patient personas and their conversion/margin profiles.
**Answer:**
1. **Cluster 0 — High-Risk Disengaged (`503` patients, `33.5%`):** Avg intent `45.6`, avg engagement `32.1`, slowest response `19.8h`, avg case value `₹402.1k`. Converts at only **`14.71%`** with **`37.18%` coded drop-off** (`₹12.74M` total margin).
2. **Cluster 1 — High-Intent Converters (`571` patients, `38.1%`):** Avg intent `75.3`, avg engagement `69.7`, fastest response `15.0h`, avg case value `₹327.0k`. Converts at **`60.25%`** with only **`10.16%` drop-off** (`₹52.20M` total margin).
3. **Cluster 2 — High-Value At-Risk (`426` patients, `28.4%`):** Avg intent `63.1`, avg engagement `55.5`, response `16.4h`, highest avg case value **`₹716.8k`**. Converts at **`31.92%`** with **`24.65%` drop-off** (`₹46.58M` total margin).

### Q43. Why is the "High-Value At-Risk" persona the highest-leverage segment for MedTourEasy?
**Answer:** High-Value At-Risk patients have an average case value of **`₹716,827`**—more than **2.19x** the case value of High-Intent Converters (`₹327,005`)—and decent intent (`63.1`), yet their completion rate is nearly half that of High-Intent Converters (`31.92%` vs `60.25%`). Because each converted High-Value patient generates roughly `₹320k+` in gross margin, even a 5–10 percentage point conversion lift in this 426-patient cohort yields massive bottom-line impact.

### Q44. How did you ensure K-Means cluster labels (`0, 1, 2`) are deterministically mapped to persona names?
**Answer:** Even with `random_state=42` and `n_init=20`, K-Means integer IDs (`0, 1, 2`) can permute across different BLAS/OS architectures. In `src/segmentation.py` (`assign_persona_names()`), we map persona names programmatically by inspecting cluster centroids: the cluster with maximum `avg_case_value_inr` is assigned `High-Value At-Risk`, the remaining cluster with higher `avg_engagement_score` is assigned `High-Intent Converters`, and the lowest-engagement cluster is assigned `High-Risk Disengaged`.

---

## Part G: SQL, Financial Scenarios & Executive Recommendations (Q45–Q50)

### Q45. How did you write the SQL query to compute both raw and strict sequential funnel conversion in a single pass (`Q1`)?
**Answer:** Using a CTE (`WITH base AS (...)`), we computed `SUM(CAST(treatment_completed AS INTEGER))` for recorded completions (`554`) and a conditional aggregation `SUM(CASE WHEN CAST(treatment_completed AS INTEGER)=1 AND CAST(quote_shared AS INTEGER)=1 THEN 1 ELSE 0 END)` for `strict_treatments` (`325`), using `NULLIF(..., 0)` in all denominators to prevent division-by-zero errors.

### Q46. How did you use SQL window functions in `sql/medtoureasy_analysis.sql`?
**Answer:**
- In **`Q7` (Drop-off distribution)**, we used `SUM(COUNT(*)) OVER ()` to compute each `(drop_off_stage, lead_source)` cell's percentage share of total coded drop-offs in a single query without a self-join.
- In **`Q9` (Provider leaderboard)**, we used `DENSE_RANK() OVER (ORDER BY 1.0*completed/NULLIF(leads,0) DESC)` to rank all 30 providers by treatment conversion rate while handling ties cleanly.

### Q47. Walk me through the exact math of the 10% Financial Recovery Scenario.
**Answer:**
1. Sum of `estimated_case_value_inr` across the `350` explicitly coded drop-offs (`drop_off_flag = 1`) = **`₹166,511,306` (`₹166.51M`)**.
2. Observed gross margin rate on the `554` completed treatments = `₹111,514,356 / ₹248,325,245 = 0.44906572` (**`44.91%`**).
3. Under a **10% recovery scenario**, `10%` of the drop-off exposure converts:
   - **Scenario Incremental Revenue:** `0.10 * ₹166,511,306 = ₹16,651,131` (**`₹16.65M`**).
   - **Scenario Incremental Gross Margin:** `₹16,651,131 * 0.44906572 = ₹7,477,452` (**`₹7.48M`**).

### Q48. Why must recovery numbers be presented as scenarios rather than forecasted revenue?
**Answer:** Two reasons: First, `estimated_case_value_inr` is a pre-treatment estimate, not a binding hospital invoice. Second, dropped-off patients may have structural barriers (e.g., clinical ineligibility or choosing a local domestic hospital) that cannot be overcome even with perfect coordinator follow-up. Labeling `₹7.48M` as a *10% recovery planning scenario* demonstrates executive maturity and prevents over-promising ROI.

### Q49. If the CEO gave you engineering bandwidth for only TWO interventions next quarter, which two would you pick?
**Answer:**
1. **Deploy Country-Tiered SLA Auto-Routing & Instant Triage (<4h response target):** Attacks the `82.8%` SLA breach rate where `54.8%` of coded drop-offs occur (`Inquiry` and `First Response` stages) and where SLA compliance is associated with a `+16.7 pp` higher consultation booking rate.
2. **72-Hour ML + Persona Escalation Desk for "High-Value At-Risk" Leads:** Routes the `426` High-Value At-Risk patients (`₹716.8k` avg case value) and borderline ML probability cases (`0.40 <= p <= 0.65`) directly to top-performing coordinators (`COORD-06`, `COORD-03`) and Tier-1 Intelligence Score hospitals (`PVD-020`, `PVD-008`, `PVD-015`).

### Q50. What are the main limitations of this project and what would you build in Phase 2?
**Answer:**
- **Limitations:** (1) Observational data prevents causal claims on SLA lift without an RCT; (2) `229` completed cases lack `quote_shared=1`, requiring CRM pipeline repair; (3) No intermediate patient sentiment metric exists for non-completers since `satisfaction_score` is post-treatment only.
- **Phase 2 Roadmap:** (1) Run a randomized controlled experiment on `<2h` rapid-response routing; (2) Implement survival analysis ( Cox Proportional Hazards / Kaplan-Meier time-to-dropoff) to model *when* a lead goes cold hour-by-hour; (3) Calibrate ML probabilities via isotonic regression and integrate live webhook scoring into the coordinator CRM.

---

## Part H: Common Interviewer Follow-Up Traps & How to Handle Them

| Interviewer Trap Question | Weak Answer (Avoid) | Strong Senior Answer (Use This) |
|---|---|---|
| *"Your quote-to-treatment conversion is 98.75%—doesn't that mean your sales team is almost perfect once a quote is shared?"* | *"Yes, once a quote is shared almost everyone completes treatment."* | *"Actually, no—that 98.75% (`554/561`) is a data-tracking artifact I uncovered during my audit. Exactly 229 completed patients have `quote_shared=0`. When we filter to strict sequential conversions (`325/561`), true quote-to-treatment conversion is **57.93%**. I reported both tables and flagged the CRM logging bypass as a P0 governance fix."* |
| *"Why didn't you use `satisfaction_score` or `drop_off_flag` in your Random Forest? Wouldn't your AUC be 0.99?"* | *"I forgot to include them / I can add them."* | *"Including them would cause catastrophic target leakage. My data quality audit proved that `satisfaction_score` is only recorded after treatment completion (missing for all 946 non-completed cases), and `drop_off_flag` is a terminal outcome label. A deployable triage model at hour 72 can only use pre-cutoff features."* |
| *"Can we tell the CFO that fixing SLA breaches will guarantee ₹166.5M in extra revenue?"* | *"Yes, ₹166.5M is the revenue we lost from drop-offs."* | *"No. ₹166.5M is the total estimated case value exposure across the 350 coded drop-offs, and our SLA test ($\chi^2 = 25.78$) is observational. In my executive memo, I framed recovery as sensitivity scenarios: a 10% conversion recovery yields **₹16.65M in revenue** and **₹7.48M in gross margin** at our observed 44.91% margin rate."* |
| *"Why didn't you use XGBoost or a Deep Neural Network for 1,500 rows?"* | *"Random Forest is always better than XGBoost."* | *"On a tabular dataset of 1,500 rows (1,200 train / 300 test), deep neural networks overfit heavily and lack interpretability. Pairing a regularized Logistic Regression baseline (`0.8193 AUC`) with a constrained Random Forest (`0.8695 AUC`, `min_samples_leaf=3`) gave strong non-linear lift, stable variance, and transparent odds-ratio + Gini explainability suitable for operations stakeholders."* |
