"""Comprehensive automated test suite for the MedTourEasy Patient Intelligence pipeline.

Covers all 9 required test domains:
1. Data loading (CSV & SQLite)
2. Data validation (Primary keys, Foreign keys, Structural missingness)
3. Financial reconciliation (patient_journey vs treatment_outcomes)
4. Funnel calculations (Raw flags vs Strict sequential conversion & 229 anomaly)
5. SLA calculations & statistical testing (Chi-square, Welch's t-test, effect sizes)
6. Feature engineering & data leakage prevention (72-hour communication cutoff, forbidden features)
7. Model pipeline (Logistic Regression & Random Forest metrics, confusion matrices, thresholds)
8. Patient segmentation (K-Means standardization, cluster quality, persona assignment)
9. SQL execution (All 11 business and governance SQL queries against SQLite)
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analytics import (
    add_sla_breach,
    compute_channel_performance,
    compute_coordinator_sla,
    compute_country_sla,
    compute_dropoff_tables,
    compute_economic_scenarios,
    compute_funnel_tables,
    compute_provider_scorecard,
    compute_treatment_economics,
    funnel,
    sla_test,
)
from src.data_quality import (
    TABLES,
    audit_foreign_keys,
    audit_primary_keys,
    detect_data_anomalies,
    load_csvs,
    load_sqlite,
    profile_all_tables,
    reconcile_csv_sqlite,
    reconcile_financials,
)
from src.modeling import (
    CATEGORICAL_FEATURES,
    FORBIDDEN_LEAKAGE_FEATURES,
    NUMERIC_FEATURES,
    prepare_modeling_dataset,
    train_and_evaluate_models,
)
from src.segmentation import (
    SEGMENTATION_FEATURES,
    build_persona_profiles,
    evaluate_cluster_counts,
)

DATA_DIR = ROOT / "data"


@pytest.fixture(scope="module")
def csv_tables():
    return load_csvs(DATA_DIR)


@pytest.fixture(scope="module")
def db_tables():
    return load_sqlite(DATA_DIR / "mte_patient_intelligence.db")


# 1. Data Loading Tests
def test_data_loading_row_counts(csv_tables, db_tables):
    expected_counts = {
        "patient_journey": 1500,
        "provider_master": 30,
        "communication_logs": 6025,
        "treatment_outcomes": 554,
        "country_reference": 12,
    }
    assert set(csv_tables.keys()) == set(TABLES)
    assert set(db_tables.keys()) == set(TABLES)
    for table, count in expected_counts.items():
        assert len(csv_tables[table]) == count
        assert len(db_tables[table]) == count


# 2. Data Validation & Governance Tests
def test_primary_and_foreign_keys(csv_tables):
    pk = audit_primary_keys(csv_tables)
    assert pk["unique_ok"].all()
    assert (pk["null_keys"] == 0).all()
    assert (pk["duplicate_keys"] == 0).all()

    fk = audit_foreign_keys(csv_tables)
    assert (fk["orphan_count"] == 0).all()


def test_structural_missingness_and_reconciliation(csv_tables, db_tables):
    dq = profile_all_tables(csv_tables)
    sat_nulls = int(
        dq.loc[
            (dq["table"] == "patient_journey") & (dq["column"] == "satisfaction_score"),
            "null_count",
        ].iloc[0]
    )
    assert sat_nulls == 946  # 1,500 - 554 completed treatments

    delay_nulls = int(
        dq.loc[
            (dq["table"] == "communication_logs")
            & (dq["column"] == "response_delay_hours"),
            "null_count",
        ].iloc[0]
    )
    assert delay_nulls == 1413
    # Every missing response_delay_hours corresponds to response_sent == 0
    cl = csv_tables["communication_logs"]
    assert (cl.loc[cl["response_delay_hours"].isna(), "response_sent"] == 0).all()

    recon = reconcile_csv_sqlite(csv_tables, db_tables)
    assert len(recon) == 67
    assert (recon["csv_rows"] == recon["db_rows"]).all()


# 3. Financial Reconciliation Tests
def test_financial_reconciliation(csv_tables):
    fin = reconcile_financials(
        csv_tables["patient_journey"], csv_tables["treatment_outcomes"]
    )
    assert len(fin) == 6
    assert bool(fin["reconciled"].all()) is True

    pj = csv_tables["patient_journey"]
    assert int(pj["actual_revenue_inr"].sum()) == 248325245
    assert int(pj["service_cost_inr"].sum()) == 136810889
    assert int((pj["actual_revenue_inr"] - pj["service_cost_inr"]).sum()) == 111514356

    econ = compute_economic_scenarios(pj)
    exp = int(
        econ.loc[
            econ["metric"] == "Drop-off estimated case-value exposure", "inr"
        ].iloc[0]
    )
    assert exp == 166511306


# 4. Funnel Calculation Tests
def test_funnel_calculations(csv_tables):
    pj = csv_tables["patient_journey"]
    f = funnel(pj)
    assert f["inquiries"] == 1500
    assert f["consultations"] == 984
    assert f["quotes"] == 561
    assert f["treatments"] == 554
    assert f["strict_treatments"] == 325
    assert f["unquoted_completions"] == 229

    raw_df, strict_df = compute_funnel_tables(pj)
    assert np.isclose(raw_df.loc[1, "conversion_pct"], 65.6)
    assert np.isclose(raw_df.loc[2, "conversion_pct"], 57.012195, atol=1e-4)
    assert np.isclose(strict_df.loc[3, "conversion_pct"], 57.932264, atol=1e-4)

    d_stage, d_source = compute_dropoff_tables(pj)
    assert int(d_stage["cases"].sum()) == 350
    assert int(d_source["dropoffs"].sum()) == 350


# 5. SLA & Statistical Hypothesis Tests
def test_sla_calculations_and_statistics(csv_tables):
    sla_df = add_sla_breach(
        csv_tables["patient_journey"], csv_tables["country_reference"]
    )
    stats = sla_test(sla_df)
    assert stats["sla_breach_count"] == 1242.0
    assert np.isclose(stats["sla_breach_rate"], 0.828)
    assert np.isclose(stats["consultation_rate_no_breach"], 0.7945736, atol=1e-5)
    assert np.isclose(stats["consultation_rate_breach"], 0.6272141, atol=1e-5)
    assert np.isclose(stats["chi2"], 25.778355, atol=1e-4)
    assert np.isclose(stats["chi2_p"], 3.82959e-07, rtol=1e-3)
    assert np.isclose(stats["t_stat"], -7.956887, atol=1e-4)
    assert stats["t_p"] < 1e-14


# 6. Provider, Coordinator, Channel & Treatment Scorecards
def test_provider_and_channel_scorecards(csv_tables):
    sc = compute_provider_scorecard(
        csv_tables["patient_journey"],
        csv_tables["provider_master"],
        csv_tables["country_reference"],
        csv_tables["treatment_outcomes"],
    )
    assert len(sc) == 30
    assert sc.iloc[0]["provider_id"] == "PVD-020"
    assert np.isclose(sc.iloc[0]["provider_intelligence_score"], 80.775075, atol=1e-4)
    assert sc.iloc[-1]["provider_id"] == "PVD-023"

    coord = compute_coordinator_sla(
        csv_tables["patient_journey"], csv_tables["country_reference"]
    )
    assert len(coord) == 15
    assert int(coord["leads"].sum()) == 1500

    ch = compute_channel_performance(csv_tables["patient_journey"])
    assert len(ch) == 6
    assert int(ch["leads"].sum()) == 1500

    te = compute_treatment_economics(csv_tables["patient_journey"])
    assert len(te) == 9
    assert int(te["completed"].sum()) == 554


# 7. Feature Engineering & Data Leakage Prevention Tests
def test_feature_engineering_and_leakage_guardrail(csv_tables):
    ml_df = prepare_modeling_dataset(
        csv_tables["patient_journey"],
        csv_tables["provider_master"],
        csv_tables["communication_logs"],
        csv_tables["country_reference"],
        cutoff_hours=72.0,
    )
    assert len(ml_df) == 1500
    for col in NUMERIC_FEATURES + CATEGORICAL_FEATURES:
        assert col in ml_df.columns
        assert col not in FORBIDDEN_LEAKAGE_FEATURES

    # Verify that passing a forbidden feature raises a ValueError
    with pytest.raises(ValueError, match="Data leakage detected"):
        train_and_evaluate_models(
            ml_df,
            numeric_features=NUMERIC_FEATURES + ["actual_revenue_inr"],
            categorical_features=CATEGORICAL_FEATURES,
        )


# 8. Supervised ML Pipeline Tests
def test_model_pipeline_evaluation(csv_tables):
    ml_df = prepare_modeling_dataset(
        csv_tables["patient_journey"],
        csv_tables["provider_master"],
        csv_tables["communication_logs"],
        csv_tables["country_reference"],
        cutoff_hours=72.0,
    )
    res = train_and_evaluate_models(ml_df)
    m_df = res["metrics_df"].set_index("model")

    # Logistic Regression exact checks
    lr = m_df.loc["Logistic Regression"]
    assert np.isclose(lr["roc_auc"], 0.819295, atol=1e-4)
    assert (int(lr["tn"]), int(lr["fp"]), int(lr["fn"]), int(lr["tp"])) == (
        136,
        53,
        25,
        86,
    )

    # Random Forest checks
    rf = m_df.loc["Random Forest"]
    assert np.isclose(rf["roc_auc"], 0.8695, atol=2e-3)
    assert (int(rf["tn"]), int(rf["fp"]), int(rf["fn"]), int(rf["tp"])) == (
        166,
        23,
        33,
        78,
    )
    assert np.isclose(rf["precision"], 0.772277, atol=1e-4)
    assert np.isclose(rf["recall"], 0.702703, atol=1e-4)

    # Feature importance top 5 set check (intent_score and response_time_hours are both ~7.4%)
    top5 = set(res["feature_importance_df"]["feature"].iloc[:5].tolist())
    assert top5 == {
        "num__engagement_score",
        "num__estimated_case_value_inr",
        "num__intent_score",
        "num__response_time_hours",
        "num__early_avg_response_delay",
    }
    assert res["feature_importance_df"]["feature"].iloc[0] == "num__engagement_score"
    assert res["feature_importance_df"]["feature"].iloc[1] == "num__estimated_case_value_inr"


# 9. K-Means Patient Segmentation Tests
def test_segmentation_personas(csv_tables):
    pj = csv_tables["patient_journey"]
    eval_df = evaluate_cluster_counts(pj, SEGMENTATION_FEATURES, k_range=range(2, 6))
    assert len(eval_df) == 4
    assert (eval_df["silhouette_score"] > 0.15).all()

    prof, pj_personas, _ = build_persona_profiles(pj, n_clusters=3, random_state=42)
    assert len(prof) == 3
    assert int(prof["patients"].sum()) == 1500
    assert set(prof["persona"]) == {
        "High-Risk Disengaged",
        "High-Intent Converters",
        "High-Value At-Risk",
    }
    by_persona = prof.set_index("persona")
    assert int(by_persona.loc["High-Risk Disengaged", "patients"]) == 503
    assert int(by_persona.loc["High-Intent Converters", "patients"]) == 571
    assert int(by_persona.loc["High-Value At-Risk", "patients"]) == 426


# 10. SQL Analytics Layer Tests
def test_sql_execution():
    conn = sqlite3.connect(DATA_DIR / "mte_patient_intelligence.db")
    try:
        sql_text = (ROOT / "sql" / "medtoureasy_analysis.sql").read_text()
        queries = [
            q.strip()
            for q in sql_text.split(";")
            if q.strip()
            and not all(l.strip().startswith("--") for l in q.strip().splitlines())
        ]
        assert len(queries) == 11
        for q in queries:
            df = pd.read_sql_query(q, conn)
            assert len(df) >= 1
    finally:
        conn.close()
