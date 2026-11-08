# Technical Defense Guide: Data Quality, Statistics, ML, Leakage, Segmentation & Financials

This document provides rigorous mathematical, statistical, and engineering defenses for every methodology, model, and assumption in the **MedTourEasy Patient Intelligence** project.

---

## 1. Data-Quality & Governance Defense

### Why didn't we impute `satisfaction_score` or `response_delay_hours` with zeros or global medians?
1. **`patient_journey.satisfaction_score` (946 / 1,500 missing = 63.07%):**
   - **Audit Finding:** Cross-tabulating `satisfaction_score.isna()` against `treatment_completed` reveals that **100% of the 554 completed cases have a non-null satisfaction score**, and **100% of the 946 non-completed cases have a null satisfaction score**.
   - **Defense:** This is **structural missingness (Missing Not At Random / post-outcome availability)**. If you include `satisfaction_score` in a pre-treatment ML pipeline and impute missing values with the median, the tree model or even a missingness indicator will immediately learn that non-missingness (or any non-median value) equals `treatment_completed = 1`, resulting in near-1.0 artificial ROC-AUC (target leakage). Therefore, `satisfaction_score` is strictly excluded from pre-treatment ML and used only for post-treatment provider benchmarking.
2. **`communication_logs.response_delay_hours` (1,413 / 6,025 missing = 23.45%):**
   - **Audit Finding:** Every single row where `response_delay_hours` is null has `response_sent = 0`.
   - **Defense:** Filling missing delay hours with `0` would tell the model that unanswered touchpoints had an instantaneous `0.0 hour` response time—inverting the true operational signal! Instead, we compute `early_response_rate = mean(response_sent)` alongside `early_avg_response_delay = mean(response_delay_hours)` (which averages over answered interactions and lets the pipeline's fold-specific median imputer handle patients with zero answered interactions in the first 72 hours).

### How did we handle the 229 unquoted treatment completions (`treatment_completed = 1, quote_shared = 0`)?
- **Audit Finding:** Out of `554` completed treatments, `325` have `quote_shared = 1` and `229` have `quote_shared = 0`.
- **Defense:** A common junior analyst mistake is either:
  1. Silently dividing `554 / 561 = 98.75%` and telling executives that "98.8% of quotes convert to treatment," which is mathematically false because 229 of those 554 numerator cases are not in the 561 denominator!
  2. Silently overwriting `quote_shared = 1` for those 229 rows, which destroys auditability and hides a major CRM tracking defect (direct hospital admissions or offline quote sharing bypassing the coordinator quote log).
- **Our Solution:** We preserve raw flags as the immutable audit record and publish two separate funnel tables (`funnel_raw_flags.csv` and `funnel_strict_sequential.csv`), reporting the true sequential quote-to-treatment rate of **`325 / 561 = 57.93%`**.

---

## 2. Statistical Testing Defense (Chi-Square & Welch's $t$-Test)

### Why use country-specific SLA baselines instead of a single global threshold?
- International medical travel markets have different timezone overlaps, language requirements, and partner desk expectations (`country_reference.csv` defines `6h` for Nigeria, Nepal, Sri Lanka; `8h` for India, Malaysia, Philippines, Tanzania, UAE; `12h` for Bangladesh, Kenya, Oman, Thailand).
- Defining $\text{SLA Breach} = \mathbb{I}(\text{response\_time\_hours} > \text{baseline\_response\_expectation\_hours})$ respects market-specific service expectations.

### Why Chi-Square ($\chi^2$) AND Welch's Two-Sample $t$-Test?
1. **Chi-Square Test of Independence ($\chi^2 = 25.78, \text{dof}=1, p = 3.83 \times 10^{-7}$):**
   - Tests the categorical contingency table between binary `sla_breach` (`True`: 1,242; `False`: 258) and binary `consultation_booked` (`1`: 984; `0`: 516).
   - **Assumptions Checked:** Independent observations (1 row per unique `patient_id`), expected cell counts $\ge 5$ in all four cells (smallest expected cell is $258 \times 516 / 1500 = 88.75 \gg 5$).
   - **Effect Size:** Cramér's $V = \sqrt{\chi^2 / N} = \sqrt{25.778 / 1500} = 0.1311$, and an absolute conversion rate gap of **-16.74 percentage points** (`62.72%` vs. `79.46%`, 95% CI: `[-22.39 pp, -11.09 pp]`).
2. **Welch's Two-Sample $t$-Test ($t = -7.96, p = 4.84 \times 10^{-15}$):**
   - Because dichotomizing a continuous variable (`response_time_hours`) into a binary SLA flag loses granular information, we also test the continuous response time distribution between booked ($n_1 = 984, \bar{x}_1 = 15.77\text{h}$) and non-booked ($n_0 = 516, \bar{x}_0 = 19.40\text{h}$) patients.
   - **Why Welch's $t$-test (`equal_var=False`) over Student's $t$-test?** Student's $t$-test assumes homoscedasticity ($\sigma_1^2 = \sigma_0^2$). With unbalanced group sizes ($984$ vs. $516$) and right-skewed response times, Welch's $t$-test adjusts degrees of freedom via the Welch–Satterthwaite equation and remains robust to unequal variances.
   - **Effect Size:** Cohen's $d = -0.431$ (medium-to-strong practical effect; mean difference **-3.63 hours**, 95% CI: `[-4.53h, -2.74h]`).

### Why Association $\neq$ Causation
- In observational CRM logs, unobserved confounders—such as inquiry arrival hour (night vs. business hours), patient clinical complexity, or coordinator workload spikes—can simultaneously delay response times and lower consultation booking. To prove causality, MedTourEasy must run an **A/B routing experiment** (randomizing incoming leads to an automated rapid-triage desk vs. standard queue).

---

## 3. Data Leakage Prevention Defense

### What is the exact prediction point (cutoff timestamp)?
- **Prediction Timestamp:** $t_0 + 72\text{ hours}$ after `inquiry_date`.
- **Business Rationale:** By hour 72, initial triage and early touchpoints have occurred, giving the model rich behavioral signals (`early_interactions`, `early_response_rate`, `early_avg_response_delay`, `early_followup_completed`) while still being early enough in the international medical travel journey (where travel lead times average 11 to 45 days) for coordinators to intervene and save at-risk cases.

### Complete Audit of Excluded Leakage Variables
| Excluded Variable | Reason for Exclusion |
|---|---|
| `actual_revenue_inr`, `service_cost_inr`, `gross_margin_inr` | Realized only after treatment completion (`>0` iff `treatment_completed == 1`). |
| `satisfaction_score` | Post-treatment survey metric; non-null iff `treatment_completed == 1`. |
| `treatment_outcomes.*` (`treatment_date`, `length_of_stay_days`, `readmission_within_30d`, `follow_up_rating`) | Post-treatment hospital outcome table. |
| `consultation_booked`, `quote_shared`, `follow_up_completed`, `current_stage` | Downstream funnel progression flags that occur across the multi-week journey after the 72h triage cutoff. |
| `drop_off_flag`, `drop_off_stage`, `reason_for_drop_off` | Terminal outcome coding (`drop_off_flag == 1` implies `treatment_completed == 0`). |
| `communication_logs` where `timestamp > inquiry_date + 72h` | Future touchpoints occurring days or weeks after inquiry (e.g., `Post-treatment follow-up` or `Travel coordination`). |

---

## 4. Supervised ML Defense: Logistic Regression vs. Random Forest

### Why pair Logistic Regression with Random Forest?
1. **Logistic Regression (`ROC-AUC = 0.8193`, `Recall = 0.7748`, `Precision = 0.6187`, `F1 = 0.6880`):**
   - Provides a linear, calibrated, directionally interpretable baseline via **log-odds coefficients** and **odds ratios ($e^{\beta_j}$)**.
   - Requires numerical standardization (`StandardScaler`) because L2 regularization penalizes coefficients by magnitude.
2. **Random Forest (`ROC-AUC = 0.8695`, `Recall = 0.7027`, `Precision = 0.7723`, `F1 = 0.7358`):**
   - Captures non-linear thresholds and high-order interactions (e.g., high `estimated_case_value_inr` in `Transplant Evaluation` or `Oncology` combined with slow `response_time_hours` and moderate `engagement_score`).
   - Outperforms Logistic Regression by **+5.02 percentage points in ROC-AUC** (`0.8695` vs. `0.8193`) and **+15.36 percentage points in Precision** (`77.23%` vs. `61.87%`) at the default `0.50` threshold.
   - Hyperparameters (`n_estimators=500`, `min_samples_leaf=3`, `max_features=0.7`, `class_weight="balanced"`) prevent deep-tree overfitting on the 1,200-row training set while stabilizing variance across trees.

### Precision vs. Recall Business Trade-Off & Threshold Tuning
- **Class Imbalance:** `36.93%` positive (`treatment_completed = 1`) vs. `63.07%` negative. Handled via stratified splitting (`stratify=y`) and inverse class weighting (`class_weight="balanced"`).
- **Cost Matrix Asymmetry:**
  - Average realized gross margin per completed treatment = **`₹111,514,356 / 554 = ₹201,289`**.
  - Cost of a coordinator follow-up intervention call/message = **~₹200–₹500** in staff time.
  - Therefore, when using the model to prioritize leads with conversion potential or flag borderline cases (`0.30 <= p <= 0.60`), **Recall is more valuable than Precision** up to the coordinator team's daily capacity constraint.
  - Shifting the Random Forest threshold from `0.50` to **`0.40`** lifts Recall from **70.27% to 78.38%** (catching 87 of 111 test-set completers instead of 78) while keeping Precision strong at **67.97%** (`F1 = 0.7280`).

---

## 5. K-Means Patient Segmentation Defense

### Why Standardize Features Before K-Means?
- K-Means minimizes within-cluster sum of squared Euclidean distances:
  $$J = \sum_{k=1}^{K} \sum_{i \in C_k} \| \mathbf{x}_i - \boldsymbol{\mu}_k \|_2^2$$
- Without `StandardScaler` ($\mu=0, \sigma=1$), `estimated_case_value_inr` (ranging from `₹50,000` to `₹1,500,000+`, variance $\sim 10^{10}$) would completely overwhelm `response_time_hours` (range `1–40`, variance $\sim 50$) and `intent_score` / `engagement_score` (range `0–100`), reducing K-Means to a 1D bucketing on rupee case value.

### Why $k = 3$ Clusters?
- Evaluating $k \in \{2, 3, 4, 5, 6\}$ shows that $k=3$ achieves strong Silhouette separation while producing three **mutually exclusive, operationally distinct personas**:
  1. **Cluster 0 — High-Risk Disengaged (`n = 503`):** Low intent (`45.6`), low engagement (`32.1`), slowest response (`19.8h`), lowest completion (`14.7%`), highest drop-off (`37.2%`).
  2. **Cluster 1 — High-Intent Converters (`n = 571`):** High intent (`75.3`), high engagement (`69.7`), fastest response (`15.0h`), highest completion (`60.2%`), lowest drop-off (`10.2%`), `₹52.20M` gross margin.
  3. **Cluster 2 — High-Value At-Risk (`n = 426`):** Massive case value (`₹716.8k` mean vs `₹327.0k` for Cluster 1), moderate intent (`63.1`) and engagement (`55.5`), but only `31.9%` completion and `24.6%` drop-off (`₹46.58M` gross margin). This is the #1 operational leverage segment.

---

## 6. Financial Impact & Scenario Defense

1. **Exact Reconciliation:**
   - Completed cases = `554`.
   - Total Actual Revenue = `₹248,325,245` (`₹248.33M`).
   - Total Service Cost = `₹136,810,889` (`₹136.81M`).
   - Total Gross Margin = `₹111,514,356` (`₹111.51M`).
   - Observed Gross Margin Percentage = `111,514,356 / 248,325,245 = 44.9066%` (`~44.9%`).
2. **Drop-Off Exposure vs. Realized Revenue:**
   - The 350 explicitly coded drop-offs have a combined `estimated_case_value_inr` of **`₹166,511,306` (`₹166.51M`)**, with the top 20% (`70` patients) representing **`₹54,398,190` (`₹54.40M`)**.
   - **Crucial Distinction:** We never claim `₹166.5M` is "lost profit" or "guaranteed recoverable revenue." Instead, we model transparent sensitivity scenarios:
     - **5% Recovery Scenario:** `₹8.33M` revenue $\rightarrow$ `₹3.74M` gross margin.
     - **10% Recovery Scenario:** `₹16.65M` revenue $\rightarrow$ `₹7.48M` gross margin.
     - **20% Recovery Scenario:** `₹33.30M` revenue $\rightarrow$ `₹14.95M` gross margin.
