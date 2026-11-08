# MedTourEasy Patient Intelligence — Interview Preparation & Technical Defense Guide

This guide prepares you to present and defend the **MedTourEasy Patient Conversion & Provider Performance Intelligence** project across Data Scientist, Machine Learning Engineer, Analytics Engineer, and Senior Data Analyst interviews.

---

## 1. Two-Minute Executive Pitch (Behavioral / Hiring Manager)

> "In my MedTourEasy Patient Intelligence project, I built an end-to-end healthcare operations analytics and machine learning system across **1,500 international patient journeys**, **6,025 communication touchpoints**, **30 partner hospitals**, and **12 source countries**.
>
> The business problem was high funnel attrition and inconsistent partner hospital performance: while **65.6%** of patient inquiries booked a consultation, only **36.9% (554 patients)** completed treatment—generating **₹248.3M in gross revenue** and **₹111.5M in gross margin** (44.9% margin), while leaving **₹166.5M in estimated case value** across **350 explicitly coded drop-offs**.
>
> First, I ran a rigorous data quality and financial reconciliation audit across CSV and SQLite sources. I discovered a critical tracking anomaly: **229 patients completed treatment with `quote_shared=0`**, which artificially inflated the naive quote-to-treatment ratio to **98.75%**. By separating raw stage flags from a strict sequential funnel, I established the true sequential quote-to-treatment rate at **57.93%**.
>
> Second, using country-specific response-time SLAs, I proved via Chi-square testing ($\chi^2 = 25.78, p = 3.83 \times 10^{-7}$) and Welch's $t$-test ($p = 4.84 \times 10^{-15}$) that **82.8%** of inquiries breached their country SLA, and SLA breaches were associated with a **16.7 percentage-point drop** in consultation booking (**62.7% vs. 79.5%**).
>
> Third, I engineered strictly pre-cutoff features—restricting communication logs to the **first 72 hours post-inquiry** and excluding post-treatment satisfaction and revenue to prevent target leakage—and trained Logistic Regression (**0.8193 ROC-AUC**) and Random Forest (**0.8695 ROC-AUC**) models, alongside a **K-Means segmentation ($k=3$)** that isolated **426 High-Value At-Risk patients** averaging **₹716.8k in case value**.
>
> Finally, I built an 11-query SQL analytics layer, a composite **Provider Intelligence Scorecard** ranking all 30 hospitals, and an interactive Streamlit dashboard mapping our findings to operational owners—where a conservative **10% drop-off recovery scenario** represents **₹16.7M in incremental revenue** and **₹7.5M in gross margin**."

---

## 2. Five-Minute Technical Deep-Dive Walkthrough

### Step 1: Data Engineering & Schema Governance (`src/data_quality.py`)
- **Relational Integrity:** Validated 5 tables (`patient_journey`: 1,500 rows; `provider_master`: 30; `communication_logs`: 6,025; `treatment_outcomes`: 554; `country_reference`: 12). Audited all 5 primary keys (`0` nulls, `0` duplicates) and 6 foreign-key relationships (`0` orphans).
- **Schema Hardening:** Discovered that `mte_patient_intelligence.db` stored all columns as `TEXT` with `PRAGMA foreign_keys=0` and no indexes. Explicitly cast numeric and date fields in all 11 SQL queries and documented DDL migration controls.
- **Structural Missingness vs. Random Missingness:**
  - `patient_journey.satisfaction_score` is missing in **946 / 1,500 (63.1%)** rows—100% aligned with non-completed cases (`treatment_completed = 0`). Imputing this into ML would introduce severe post-treatment target leakage.
  - `communication_logs.response_delay_hours` is missing in **1,413 / 6,025 (23.5%)** rows—100% aligned with `response_sent = 0`. Filling with `0` would falsely treat unanswered messages as instantaneous responses.
- **Financial Reconciliation:** Verified that all 554 completed cases in `patient_journey` match `treatment_outcomes` 1-to-1, reconciling **₹248,325,245** in actual revenue, **₹136,810,889** in service cost, and **₹111,514,356** in gross margin with zero discrepancy.

### Step 2: Funnel Reconciliation & Statistical Hypothesis Testing (`src/analytics.py`)
- **Dual Funnel Accounting:** Exposed the 229 unquoted completions (`treatment_completed=1, quote_shared=0`) and reported both Raw Flags (`554 / 561 = 98.75%`) and Strict Sequential (`325 / 561 = 57.93%`).
- **Country-Specific SLA Testing:** Merged `baseline_response_expectation_hours` (`6h`, `8h`, `12h`) from `country_reference`. Defined `sla_breach = response_time_hours > baseline_response_expectation_hours`.
  - **Chi-Square Test of Independence:** $\chi^2 = 25.78, \text{dof}=1, p = 3.83 \times 10^{-7}$, Cramér's $V = 0.131$.
  - **Welch's Two-Sample $t$-Test:** Booked mean `15.77h` vs. Not-Booked mean `19.40h` ($\Delta = -3.63\text{h}, t = -7.96, p = 4.84 \times 10^{-15}$, Cohen's $d = -0.431$). Used Welch's $t$-test rather than Student's $t$-test to handle unequal variances and sample sizes ($n_1=984, n_0=516$).

### Step 3: Provider Intelligence Composite Scorecard (`src/analytics.py`, `sql/medtoureasy_analysis.sql`)
- Designed a multi-dimensional composite score (`0–100`) to prevent gaming on a single metric:
  $$\text{Provider Intelligence Score} = 0.30 \cdot S_{\text{conv}} + 0.20 \cdot S_{\text{SLA}} + 0.15 \cdot S_{\text{followup}} + 0.15 \cdot S_{\text{sat}} + 0.20 \cdot S_{\text{margin/lead}}$$
- Identified `PVD-020` as #1 overall (`80.78` score, `52.7%` conversion, `72.7%` SLA adherence, `5.85h` avg response), while diagnosing `PVD-007` (`52.0%` conversion but only `18.0%` SLA adherence) as an intake-bottleneck hospital rather than a pure benchmark.

### Step 4: Leakage-Free Supervised ML (`src/modeling.py`)
- **Prediction Point:** Triage at **72 hours post-inquiry**.
- **Feature Pipeline:** 15 numeric features + 7 categorical features processed inside a `scikit-learn` `ColumnTransformer` (`SimpleImputer` + `StandardScaler` for numeric in Logistic Regression; `SimpleImputer` + `OneHotEncoder(handle_unknown="ignore")` for categorical) wrapped in a `Pipeline` so imputation/scaling statistics are fit strictly on `X_train` ($N=1,200$).
- **Results on Stratified Test Set ($N=300$):**
  - **Logistic Regression (`class_weight="balanced"`):** ROC-AUC `0.8193`, Precision `0.6187`, Recall `0.7748`, F1 `0.6880`.
  - **Random Forest (`n_estimators=500, min_samples_leaf=3, max_features=0.7, class_weight="balanced"`):** ROC-AUC `0.8695`, Precision `0.7723`, Recall `0.7027`, F1 `0.7358`.
- **Threshold Optimization:** Demonstrated that shifting the Random Forest decision threshold from `0.50` to `0.40` increases Recall from `70.27%` to `78.38%` (`F1 = 0.7280`), aligning with asymmetric healthcare unit economics where missing a convertible patient costs ~`₹201k` in margin.

### Step 5: Unsupervised Patient Segmentation (`src/segmentation.py`)
- Standardized 4 continuous features (`intent_score`, `response_time_hours`, `engagement_score`, `estimated_case_value_inr`) using `StandardScaler` so `estimated_case_value_inr` (in hundreds of thousands of rupees) did not dominate Euclidean distance.
- Evaluated $k \in \{2..6\}$ via Inertia, Silhouette Score, and Davies-Bouldin Index; selected $k=3$ for operational actionability:
  - **Cluster 0 — High-Risk Disengaged (`503` patients):** `14.7%` completion, `37.2%` drop-off, `19.8h` response time.
  - **Cluster 1 — High-Intent Converters (`571` patients):** `60.2%` completion, `10.2%` drop-off, `₹52.2M` gross margin.
  - **Cluster 2 — High-Value At-Risk (`426` patients):** `₹716.8k` avg case value, `31.9%` completion, `24.6%` drop-off, `₹46.6M` gross margin.

---

## 3. End-to-End Architecture Explanation

```text
+-----------------------------------------------------------------------------------+
|                        1. DATA SOURCES (CSV & SQLite DB)                          |
|  patient_journey (1,500) | provider_master (30) | communication_logs (6,025)      |
|  treatment_outcomes (554)| country_reference (12)| mte_patient_intelligence.db    |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                2. DATA GOVERNANCE & RECONCILIATION (src/data_quality.py)          |
|  - PK/FK Integrity Audits (0 Orphans)   - CSV vs SQLite Normalization Checks      |
|  - Structural Missingness Profiling     - Exact Financial & Margin Reconciliation |
|  - Funnel Stage Anomaly Detection (229 Unquoted Completions Flagged)              |
+-----------------------------------------+-----------------------------------------+
                                          |
                    +---------------------+---------------------+
                    |                                           |
                    v                                           v
+---------------------------------------+   +---------------------------------------+
| 3A. ANALYTICS & SQL LAYER             |   | 3B. ML & SEGMENTATION LAYER           |
| (src/analytics.py & sql/*.sql)        |   | (src/modeling.py & segmentation.py)   |
| - Raw vs Strict Sequential Funnel     |   | - 72h Pre-Cutoff Feature Engineering  |
| - Country SLA Chi-Square & Welch t    |   | - Leakage Guardrail Validation        |
| - Composite Provider Scorecard (0-100)|   | - Logistic Regression (AUC: 0.8193)   |
| - Channel & Specialty Unit Economics  |   | - Random Forest (AUC: 0.8695)         |
| - 11 Production SQLite Queries        |   | - Standardized K-Means Personas (k=3) |
+-------------------+-------------------+   +-------------------+-------------------+
                    |                                           |
                    +---------------------+---------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|              4. DECISION SUPPORT & DELIVERY LAYER (outputs/ & dashboard/)         |
|  - 18 Reconciled CSV Artifacts          - 16-Sheet Executive Excel Workbook       |
|  - 7 Publication-Quality EDA Figures    - Interactive 6-Page Streamlit Dashboard  |
|  - Executive Recommendation Memo        - 11 Automated Pytest Validation Suites   |
+-----------------------------------------------------------------------------------+
```
