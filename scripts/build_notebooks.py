"""Script to build and execute all 5 production Jupyter notebooks with rich outputs."""
from __future__ import annotations

from pathlib import Path
import io
import contextlib
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell, new_output

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "notebooks"


def execute_notebook_inprocess(nb: nbformat.NotebookNode, workdir: Path) -> nbformat.NotebookNode:
    """Execute all code cells in-process and capture stdout and display(DataFrame) outputs."""
    import os
    old_cwd = Path.cwd()
    os.chdir(workdir)
    ns = {"__name__": "__main__"}

    def custom_display(obj):
        outputs = ns.get("_current_outputs", [])
        if hasattr(obj, "_repr_html_"):
            outputs.append(
                new_output(
                    output_type="display_data",
                    data={"text/plain": repr(obj), "text/html": obj._repr_html_()},
                    metadata={},
                )
            )
        else:
            outputs.append(
                new_output(
                    output_type="display_data",
                    data={"text/plain": repr(obj)},
                    metadata={},
                )
            )

    ns["display"] = custom_display
    try:
        exec_count = 1
        for cell in nb.cells:
            if cell.cell_type != "code":
                continue
            cell.execution_count = exec_count
            exec_count += 1
            buf = io.StringIO()
            cell_outputs = []
            ns["_current_outputs"] = cell_outputs
            with contextlib.redirect_stdout(buf):
                exec(cell.source, ns)
            stdout_val = buf.getvalue()
            final_outputs = []
            if stdout_val:
                final_outputs.append(new_output(output_type="stream", name="stdout", text=stdout_val))
            final_outputs.extend(cell_outputs)
            cell.outputs = final_outputs
    finally:
        os.chdir(old_cwd)
    return nb


def make_nb01() -> nbformat.NotebookNode:
    nb = new_notebook()
    nb.cells = [
        new_markdown_cell(
            "# 01 — Data Quality, Schema Governance & Financial Reconciliation Audit\n\n"
            "## Objective\n"
            "Audit all five relational tables in the MedTourEasy Patient Intelligence dataset across CSV and SQLite sources:\n"
            "1. Verify row counts, column data types, missing values, and unique cardinalities.\n"
            "2. Audit primary-key uniqueness and foreign-key referential integrity.\n"
            "3. Reconcile CSV records against `mte_patient_intelligence.db`.\n"
            "4. Reconcile completed treatments, actual revenue, service cost, and gross margin between `patient_journey` and `treatment_outcomes`.\n"
            "5. Document structural missingness and funnel stage tracking anomalies (`229` completed treatments with `quote_shared=0`)."
        ),
        new_code_cell(
            "from pathlib import Path\n"
            "import sys\n"
            "import pandas as pd\n"
            "import numpy as np\n\n"
            "ROOT = Path.cwd()\n"
            "if not (ROOT / 'src').exists() and (ROOT.parent / 'src').exists():\n"
            "    ROOT = ROOT.parent\n"
            "sys.path.insert(0, str(ROOT))\n"
            "DATA = ROOT / 'data'\n\n"
            "from src.data_quality import (\n"
            "    load_csvs,\n"
            "    load_sqlite,\n"
            "    profile_all_tables,\n"
            "    audit_primary_keys,\n"
            "    audit_foreign_keys,\n"
            "    reconcile_csv_sqlite,\n"
            "    reconcile_financials,\n"
            "    detect_data_anomalies,\n"
            ")"
        ),
        new_code_cell(
            "csv_tables = load_csvs(DATA)\n"
            "db_tables = load_sqlite(DATA / 'mte_patient_intelligence.db')\n"
            "for name, df in csv_tables.items():\n"
            "    print(f'{name:22s} | CSV shape: {str(df.shape):12s} | SQLite shape: {db_tables[name].shape}')"
        ),
        new_markdown_cell("## 1. Primary Key & Foreign Key Integrity Audits"),
        new_code_cell(
            "pk_audit = audit_primary_keys(csv_tables)\n"
            "display(pk_audit)\n"
            "fk_audit = audit_foreign_keys(csv_tables)\n"
            "display(fk_audit)"
        ),
        new_markdown_cell("## 2. Column-Level Data Quality Profile & Structural Missingness"),
        new_code_cell(
            "dq_profile = profile_all_tables(csv_tables)\n"
            "display(dq_profile[dq_profile['null_count'] > 0])\n"
            "display(dq_profile.head(26))"
        ),
        new_markdown_cell("## 3. Financial Reconciliation (`patient_journey` vs. `treatment_outcomes`)"),
        new_code_cell(
            "fin_recon = reconcile_financials(csv_tables['patient_journey'], csv_tables['treatment_outcomes'])\n"
            "display(fin_recon)"
        ),
        new_markdown_cell("## 4. Automated Governance & Anomaly Log"),
        new_code_cell(
            "anomalies = detect_data_anomalies(csv_tables)\n"
            "display(anomalies)"
        ),
    ]
    return nb


def make_nb02() -> nbformat.NotebookNode:
    nb = new_notebook()
    nb.cells = [
        new_markdown_cell(
            "# 02 — Exploratory Data Analysis, Patient Funnel & SLA Statistical Testing\n\n"
            "## Objective\n"
            "1. Reconcile the patient conversion funnel (`Inquiry -> Consultation -> Quote -> Treatment Completion`) and separate raw stage flags from strict sequential conversion.\n"
            "2. Analyze drop-off stages, reasons, and acquisition channels.\n"
            "3. Perform statistical hypothesis testing (Chi-square test of independence & Welch's two-sample t-test) on country-specific SLA breaches vs. consultation booking."
        ),
        new_code_cell(
            "from pathlib import Path\n"
            "import sys\n"
            "import pandas as pd\n"
            "import numpy as np\n\n"
            "ROOT = Path.cwd()\n"
            "if not (ROOT / 'src').exists() and (ROOT.parent / 'src').exists():\n"
            "    ROOT = ROOT.parent\n"
            "sys.path.insert(0, str(ROOT))\n"
            "DATA = ROOT / 'data'\n\n"
            "from src.data_quality import load_csvs\n"
            "from src.analytics import (\n"
            "    add_sla_breach,\n"
            "    funnel,\n"
            "    compute_funnel_tables,\n"
            "    compute_dropoff_tables,\n"
            "    sla_test,\n"
            "    format_sla_hypothesis_table,\n"
            "    compute_country_sla,\n"
            ")"
        ),
        new_code_cell(
            "tables = load_csvs(DATA)\n"
            "pj = tables['patient_journey']\n"
            "cr = tables['country_reference']\n\n"
            "funnel_raw, funnel_strict = compute_funnel_tables(pj)\n"
            "print('=== Raw Flag Funnel ===')\n"
            "display(funnel_raw)\n"
            "print('=== Strict Sequential Funnel (Requires quote_shared=1) ===')\n"
            "display(funnel_strict)"
        ),
        new_markdown_cell("## 1. Drop-Off Stage & Reason Breakdown"),
        new_code_cell(
            "dropoff_stage, dropoff_source = compute_dropoff_tables(pj)\n"
            "display(dropoff_stage)\n"
            "display(dropoff_source)\n\n"
            "reasons = (\n"
            "    pj[pj['drop_off_flag'] == 1]\n"
            "    .groupby('reason_for_drop_off', as_index=False)\n"
            "    .agg(cases=('patient_id', 'count'), exposure_inr=('estimated_case_value_inr', 'sum'))\n"
            "    .sort_values('cases', ascending=False)\n"
            ")\n"
            "display(reasons)"
        ),
        new_markdown_cell("## 2. Statistical Testing: Response-Time SLA Breach vs. Consultation Booking"),
        new_code_cell(
            "sla_df = add_sla_breach(pj, cr)\n"
            "stats = sla_test(sla_df)\n"
            "display(format_sla_hypothesis_table(stats))\n"
            "print(f\"Cramer's V: {stats['cramers_v']:.4f} | Cohen's d: {stats['cohens_d']:.4f}\")\n"
            "print(f\"95% CI for Consultation Rate Gap: [{stats['consultation_rate_gap_ci_95'][0]*100:.2f}%, {stats['consultation_rate_gap_ci_95'][1]*100:.2f}%]\")"
        ),
        new_markdown_cell("## 3. Country-Wise SLA & Conversion Performance"),
        new_code_cell(
            "country_sla = compute_country_sla(pj, cr)\n"
            "display(country_sla.sort_values('sla_breach_rate', ascending=False))"
        ),
    ]
    return nb


def make_nb03() -> nbformat.NotebookNode:
    nb = new_notebook()
    nb.cells = [
        new_markdown_cell(
            "# 03 — SQL Analytics, Provider Intelligence Scorecard & Unit Economics\n\n"
            "## Objective\n"
            "1. Execute the 11 production SQL queries in `sql/medtoureasy_analysis.sql` against `mte_patient_intelligence.db`.\n"
            "2. Compute the composite **Provider Intelligence Score** across all 30 partner hospitals.\n"
            "3. Benchmark 15 care coordinators, 6 acquisition channels, and 9 treatment specialties."
        ),
        new_code_cell(
            "from pathlib import Path\n"
            "import sqlite3\n"
            "import sys\n"
            "import pandas as pd\n\n"
            "ROOT = Path.cwd()\n"
            "if not (ROOT / 'src').exists() and (ROOT.parent / 'src').exists():\n"
            "    ROOT = ROOT.parent\n"
            "sys.path.insert(0, str(ROOT))\n"
            "DATA = ROOT / 'data'\n\n"
            "from src.data_quality import load_csvs\n"
            "from src.analytics import (\n"
            "    compute_provider_scorecard,\n"
            "    compute_coordinator_sla,\n"
            "    compute_channel_performance,\n"
            "    compute_treatment_economics,\n"
            ")"
        ),
        new_code_cell(
            "conn = sqlite3.connect(DATA / 'mte_patient_intelligence.db')\n"
            "sql_text = (ROOT / 'sql' / 'medtoureasy_analysis.sql').read_text()\n"
            "queries = [q.strip() for q in sql_text.split(';') if q.strip() and not all(l.strip().startswith('--') for l in q.strip().splitlines())]\n"
            "print(f'Loaded {len(queries)} SQL queries from medtoureasy_analysis.sql')\n"
            "for idx, q in enumerate(queries, 1):\n"
            "    res = pd.read_sql_query(q, conn)\n"
            "    print(f'Query {idx:02d} returned {res.shape[0]} rows x {res.shape[1]} cols')\n"
            "conn.close()"
        ),
        new_markdown_cell("## 1. Provider Performance Scorecard & Composite Intelligence Ranking"),
        new_code_cell(
            "tables = load_csvs(DATA)\n"
            "provider_sc = compute_provider_scorecard(\n"
            "    tables['patient_journey'], tables['provider_master'], tables['country_reference'], tables['treatment_outcomes']\n"
            ")\n"
            "print('=== Top 10 Providers by Composite Intelligence Score ===')\n"
            "display(provider_sc.head(10))\n"
            "print('=== Bottom 5 Providers (Intervention Candidates) ===')\n"
            "display(provider_sc.tail(5))"
        ),
        new_markdown_cell("## 2. Coordinator SLA & Acquisition Channel Efficiency"),
        new_code_cell(
            "coord_df = compute_coordinator_sla(tables['patient_journey'], tables['country_reference'])\n"
            "display(coord_df)\n\n"
            "channel_df = compute_channel_performance(tables['patient_journey'])\n"
            "display(channel_df)\n\n"
            "econ_df = compute_treatment_economics(tables['patient_journey'])\n"
            "display(econ_df)"
        ),
    ]
    return nb


def make_nb04() -> nbformat.NotebookNode:
    nb = new_notebook()
    nb.cells = [
        new_markdown_cell(
            "# 04 — Supervised ML: Pre-Treatment Completion Prediction & Leakage Prevention\n\n"
            "## Objective\n"
            "1. Engineer strictly pre-cutoff features (patient attributes at inquiry, provider historical baselines, country SLA baselines, and early communication logs within the first **72 hours**).\n"
            "2. Exclude all post-treatment and target-leaking variables (`actual_revenue_inr`, `service_cost_inr`, `satisfaction_score`, stage/drop-off flags).\n"
            "3. Train and compare **Logistic Regression** and **Random Forest** on an 80/20 stratified split.\n"
            "4. Analyze classification thresholds (`0.30` to `0.60`) and feature importances."
        ),
        new_code_cell(
            "from pathlib import Path\n"
            "import sys\n"
            "import pandas as pd\n\n"
            "ROOT = Path.cwd()\n"
            "if not (ROOT / 'src').exists() and (ROOT.parent / 'src').exists():\n"
            "    ROOT = ROOT.parent\n"
            "sys.path.insert(0, str(ROOT))\n"
            "DATA = ROOT / 'data'\n\n"
            "from src.data_quality import load_csvs\n"
            "from src.modeling import (\n"
            "    NUMERIC_FEATURES,\n"
            "    CATEGORICAL_FEATURES,\n"
            "    FORBIDDEN_LEAKAGE_FEATURES,\n"
            "    prepare_modeling_dataset,\n"
            "    train_and_evaluate_models,\n"
            ")"
        ),
        new_code_cell(
            "tables = load_csvs(DATA)\n"
            "ml_df = prepare_modeling_dataset(\n"
            "    tables['patient_journey'],\n"
            "    tables['provider_master'],\n"
            "    tables['communication_logs'],\n"
            "    tables['country_reference'],\n"
            "    cutoff_hours=72.0,\n"
            ")\n"
            "print('Numeric features (15):', NUMERIC_FEATURES)\n"
            "print('Categorical features (7):', CATEGORICAL_FEATURES)\n"
            "print('Excluded leakage columns:', FORBIDDEN_LEAKAGE_FEATURES)"
        ),
        new_markdown_cell("## 1. Model Comparison & Threshold Analysis"),
        new_code_cell(
            "results = train_and_evaluate_models(ml_df)\n"
            "print('=== Test Set Model Performance (80/20 Stratified Split, n_test=300) ===')\n"
            "display(results['metrics_df'])\n\n"
            "print('=== Random Forest Operational Threshold Analysis ===')\n"
            "display(results['thresholds_df'])"
        ),
        new_markdown_cell("## 2. Feature Importance & Interpretability"),
        new_code_cell(
            "print('=== Top 15 Random Forest Features ===')\n"
            "display(results['feature_importance_df'].head(15))\n\n"
            "print('=== Top 15 Logistic Regression Standardized Coefficients & Odds Ratios ===')\n"
            "display(results['logistic_coefficients_df'].head(15))"
        ),
    ]
    return nb


def make_nb05() -> nbformat.NotebookNode:
    nb = new_notebook()
    nb.cells = [
        new_markdown_cell(
            "# 05 — K-Means Patient Segmentation, Personas & Financial Scenarios\n\n"
            "## Objective\n"
            "1. Standardize core behavioral and value features (`intent_score`, `response_time_hours`, `engagement_score`, `estimated_case_value_inr`).\n"
            "2. Evaluate cluster counts ($k \\in \\{2, 3, 4, 5, 6\\}$) using Inertia, Silhouette Score, and Davies-Bouldin Index.\n"
            "3. Profile the 3 operational personas (**High-Risk Disengaged**, **High-Intent Converters**, **High-Value At-Risk**).\n"
            "4. Quantify drop-off case value exposure and clearly labeled recovery scenarios."
        ),
        new_code_cell(
            "from pathlib import Path\n"
            "import sys\n"
            "import pandas as pd\n\n"
            "ROOT = Path.cwd()\n"
            "if not (ROOT / 'src').exists() and (ROOT.parent / 'src').exists():\n"
            "    ROOT = ROOT.parent\n"
            "sys.path.insert(0, str(ROOT))\n"
            "DATA = ROOT / 'data'\n\n"
            "from src.data_quality import load_csvs\n"
            "from src.segmentation import (\n"
            "    SEGMENTATION_FEATURES,\n"
            "    evaluate_cluster_counts,\n"
            "    build_persona_profiles,\n"
            ")\n"
            "from src.analytics import compute_economic_scenarios"
        ),
        new_code_cell(
            "tables = load_csvs(DATA)\n"
            "pj = tables['patient_journey']\n\n"
            "cluster_eval = evaluate_cluster_counts(pj)\n"
            "print('=== Cluster Quality Evaluation (k = 2..6) ===')\n"
            "display(cluster_eval)"
        ),
        new_markdown_cell("## 1. Operational Persona Profiles ($k=3$)"),
        new_code_cell(
            "persona_profiles, pj_personas, km_model = build_persona_profiles(pj, n_clusters=3, random_state=42)\n"
            "display(persona_profiles)"
        ),
        new_markdown_cell("## 2. Financial Exposure & Recovery Scenario Modeling"),
        new_code_cell(
            "scenarios = compute_economic_scenarios(pj)\n"
            "display(scenarios)"
        ),
    ]
    return nb


def main():
    notebooks = {
        "01_data_quality_report.ipynb": make_nb01(),
        "02_exploratory_patient_funnel_analysis.ipynb": make_nb02(),
        "03_sql_provider_scorecard.ipynb": make_nb03(),
        "04_modeling_dropoff_and_completion.ipynb": make_nb04(),
        "05_segmentation_and_recommendations.ipynb": make_nb05(),
    }
    for fname, nb in notebooks.items():
        path = NB_DIR / fname
        execute_notebook_inprocess(nb, NB_DIR)
        with open(path, "w", encoding="utf-8") as f:
            nbformat.write(nb, f)
        print(f"Executed and saved: {path}")


if __name__ == "__main__":
    main()
