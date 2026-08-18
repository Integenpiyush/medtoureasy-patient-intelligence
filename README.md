# MedTourEasy Patient Conversion & Provider Performance Intelligence

## Project
End-to-end healthcare operations analytics across **1,500 international patient journeys**, covering data governance, funnel conversion, provider performance, SLA analysis, predictive completion risk, K-Means segmentation, SQL analytics, and executive recommendations.

The project scope follows the supplied MedTourEasy PRD: data quality/reconciliation, funnel analysis, provider benchmarking, statistical testing, supervised ML, segmentation, SQL analytics, and a management-ready recommendation memo. The PRD defines consultation conversion, treatment completion, SLA breach, communication coverage, gross margin, and a provider intelligence score as core KPIs.

## Key audited findings

| KPI | Result |
|---|---:|
| Patient journeys | **1,500** |
| Consultations booked | **984 (65.6%)** |
| Quotes shared | **561 (57.0% of consultations)** |
| Treatment completed flag | **554 (36.9% of inquiries)** |
| Explicitly coded drop-offs | **350** |
| Inquiries without consultation | **516** |
| Completed patients missing `quote_shared=1` | **229** |
| SLA breach rate | **82.8%** |
| Consultation rate: no SLA breach | **79.5%** |
| Consultation rate: SLA breach | **62.7%** |
| Chi-square p-value | **3.83e-07** |
| Welch t-test p-value | **4.84e-15** |
| Logistic Regression ROC-AUC | **0.8193** |
| Random Forest ROC-AUC | **0.8695** |
| Observed gross revenue | **₹248.3M** |
| Observed gross margin | **₹111.5M** |
| Drop-off estimated case-value exposure | **₹166.5M** |

### Important reconciliation issue
There are **229 patients marked `treatment_completed=1` while `quote_shared=0`**. Therefore, the raw quote-to-treatment ratio of 98.75% is not a valid sequential funnel KPI. The strict sequential view has **325 completed cases with a quote flag**, giving **57.9% quote-to-treatment conversion**. This is treated as a data-tracking anomaly rather than silently corrected.

### SLA evidence
SLA breach is defined using each patient's country baseline. Breached cases booked consultations at **62.7%**, versus **79.5%** for non-breached cases: a **16.7 percentage-point gap**. The chi-square test is significant (χ²=25.78, p<0.001). A Welch t-test also shows booked cases had lower mean response time (**15.77h vs 19.40h**, p<0.001). These results establish association, not causation.

### ML
The Random Forest outperformed the interpretable Logistic Regression baseline on the fixed 80/20 stratified test split. The leading operational features were engagement score, estimated case value, intent score, response time, and early communication response delay.

### Segmentation
K-Means produced three operational personas:
- **High-Risk Disengaged:** lowest intent/engagement, slowest response, lowest completion.
- **High-Intent Converters:** highest intent/engagement, fastest response, highest completion.
- **High-Value At-Risk:** highest case value, but materially weaker conversion than high-intent converters.

### Economic framing
The 350 explicitly coded drop-offs represent **₹166.5M of estimated case value exposure**. This is not automatically recoverable revenue. A scenario in which 10% of that value converts would represent **₹16.7M revenue**, and at the observed completed-case margin rate of 44.9%, approximately **₹7.5M gross margin**. This is a planning scenario, not an observed outcome.

## Repository structure

```text
medtoureasy_patient_intelligence/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   └── README.md
├── docs/
│   ├── PROJECT_SCOPE.md
│   └── ASSUMPTIONS_LOG.md
├── notebooks/
│   ├── 01_data_quality_report.ipynb
│   ├── 02_exploratory_patient_funnel_analysis.ipynb
│   ├── 03_sql_provider_scorecard.ipynb
│   ├── 04_modeling_dropoff_and_completion.ipynb
│   └── 05_segmentation_and_recommendations.ipynb
├── sql/
│   └── medtoureasy_analysis.sql
├── src/
│   ├── __init__.py
│   ├── data_quality.py
│   ├── analytics.py
│   ├── modeling.py
│   └── segmentation.py
├── scripts/
│   └── run_pipeline.py
├── outputs/
│   ├── data_quality_profile.csv
│   ├── financial_reconciliation.csv
│   ├── funnel_raw_flags.csv
│   ├── funnel_strict_sequential.csv
│   ├── dropoff_stage.csv
│   ├── dropoff_source.csv
│   ├── provider_scorecard.csv
│   ├── coordinator_sla.csv
│   ├── channel_performance.csv
│   ├── treatment_economics.csv
│   ├── country_sla.csv
│   ├── model_metrics.csv
│   ├── model_thresholds.csv
│   ├── random_forest_feature_importance.csv
│   ├── persona_profiles.csv
│   ├── economic_impact_scenarios.csv
│   └── executive_dashboard.xlsx
└── reports/
    ├── data_quality_summary.md
    └── executive_recommendation_memo.md
```

## Reproducibility
1. Put the supplied CSV files and `mte_patient_intelligence.db` in the `data/` directory.
2. Create a Python 3.10+ environment.
3. Install `requirements.txt`.
4. Run `python scripts/run_pipeline.py`.
5. Open the five notebooks for the detailed workflow.

Raw patient-level healthcare data should generally **not** be committed to a public GitHub repository. The `.gitignore` therefore excludes the supplied CSV/SQLite data files by default.

## Limitations
- The dataset is observational; SLA tests show association, not causation.
- `satisfaction_score` is a post-treatment outcome and is excluded from the pre-treatment predictive feature set.
- Communication features are restricted to the first 72 hours after inquiry to reduce target leakage.
- The supplied SQLite schema stores fields as TEXT and does not declare PK/FK constraints; production deployment should use typed columns, constraints, indexes, and validation.
- Revenue-recovery figures are scenario estimates unless supported by an approved conversion-lift assumption.
