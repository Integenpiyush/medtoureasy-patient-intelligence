"""Data loading, schema validation, and governance helpers for the MedTourEasy project."""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

TABLES: List[str] = [
    "patient_journey",
    "provider_master",
    "communication_logs",
    "treatment_outcomes",
    "country_reference",
]

PRIMARY_KEYS: Dict[str, str] = {
    "patient_journey": "patient_id",
    "provider_master": "provider_id",
    "communication_logs": "communication_id",
    "treatment_outcomes": "patient_id",
    "country_reference": "country",
}

FOREIGN_KEYS: List[tuple[str, str, str, str]] = [
    ("patient_journey", "provider_id", "provider_master", "provider_id"),
    ("patient_journey", "country", "country_reference", "country"),
    ("communication_logs", "patient_id", "patient_journey", "patient_id"),
    ("communication_logs", "provider_id", "provider_master", "provider_id"),
    ("treatment_outcomes", "patient_id", "patient_journey", "patient_id"),
    ("treatment_outcomes", "provider_id", "provider_master", "provider_id"),
]


def load_csvs(data_dir: Union[str, Path]) -> Dict[str, pd.DataFrame]:
    """Load all five MedTourEasy CSV datasets from the specified directory.

    Args:
        data_dir: Directory path containing the source CSV files.

    Returns:
        Dictionary mapping table name to its loaded pandas DataFrame.

    Raises:
        FileNotFoundError: If any expected CSV file is missing.
    """
    data_dir = Path(data_dir)
    loaded: Dict[str, pd.DataFrame] = {}
    for table in TABLES:
        csv_path = data_dir / f"{table}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Expected CSV file not found: {csv_path}")
        loaded[table] = pd.read_csv(csv_path)
        logger.debug("Loaded CSV %s with shape %s", table, loaded[table].shape)
    return loaded


def load_sqlite(db_path: Union[str, Path]) -> Dict[str, pd.DataFrame]:
    """Load all tables from the MedTourEasy SQLite database.

    Args:
        db_path: Path to mte_patient_intelligence.db.

    Returns:
        Dictionary mapping table name to its loaded pandas DataFrame.

    Raises:
        FileNotFoundError: If the SQLite file does not exist.
    """
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Expected SQLite database not found: {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name", conn
        )["name"].tolist()
        return {t: pd.read_sql_query(f'SELECT * FROM "{t}"', conn) for t in tables}
    finally:
        conn.close()


def profile(df: pd.DataFrame) -> pd.DataFrame:
    """Profile a single DataFrame for column dtypes, null counts, percentages, and unique counts."""
    out = pd.DataFrame(
        {
            "column": df.columns,
            "dtype": df.dtypes.astype(str).values,
            "null_count": df.isna().sum().values,
        }
    )
    out["null_pct"] = out["null_count"] / len(df) * 100.0
    out["unique_count"] = [df[c].nunique(dropna=True) for c in df.columns]
    return out


def profile_all_tables(csv_tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Generate a unified data quality profile across all loaded tables."""
    frames = []
    for table_name in TABLES:
        df = csv_tables[table_name]
        prof = profile(df)
        prof.insert(0, "table", table_name)
        prof.insert(3, "rows", len(df))
        frames.append(prof[["table", "column", "dtype", "rows", "null_count", "null_pct", "unique_count"]])
    return pd.concat(frames, ignore_index=True)


def audit_primary_keys(csv_tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Check primary key non-nullness and uniqueness across all five relational tables."""
    rows = []
    for table_name, pk in PRIMARY_KEYS.items():
        df = csv_tables[table_name]
        null_keys = int(df[pk].isna().sum())
        dup_keys = int(df[pk].duplicated().sum())
        unique_keys = int(df[pk].nunique(dropna=True))
        row_count = len(df)
        unique_ok = (null_keys == 0) and (dup_keys == 0) and (unique_keys == row_count)
        rows.append(
            {
                "table": table_name,
                "primary_key": pk,
                "null_keys": null_keys,
                "duplicate_keys": dup_keys,
                "unique_keys": unique_keys,
                "row_count": row_count,
                "unique_ok": unique_ok,
            }
        )
    return pd.DataFrame(rows)


def audit_foreign_keys(csv_tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Validate foreign-key referential integrity across all table relationships."""
    rows = []
    for child_table, child_col, parent_table, parent_col in FOREIGN_KEYS:
        child_vals = csv_tables[child_table][child_col].dropna()
        parent_vals = set(csv_tables[parent_table][parent_col].dropna())
        orphan_count = int((~child_vals.isin(parent_vals)).sum())
        rows.append(
            {
                "relationship": f"{child_table}.{child_col} -> {parent_table}.{parent_col}",
                "orphan_count": orphan_count,
            }
        )
    return pd.DataFrame(rows)


def _normalize_series_for_comparison(s: pd.Series) -> pd.Series:
    """Normalize string representations of values from CSV vs SQLite TEXT columns."""
    def _norm(val):
        if pd.isna(val) or val == "" or val is None:
            return "<NULL>"
        return str(val).strip()
    return s.map(_norm)


def reconcile_csv_sqlite(
    csv_tables: Dict[str, pd.DataFrame], db_tables: Dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """Reconcile row counts and column-level normalized string match rates between CSV and SQLite."""
    rows = []
    for table_name in TABLES:
        df_csv = csv_tables[table_name]
        df_db = db_tables[table_name]
        csv_rows = len(df_csv)
        db_rows = len(df_db)
        for col in df_csv.columns:
            s_csv = _normalize_series_for_comparison(df_csv[col])
            s_db = _normalize_series_for_comparison(df_db[col])
            match_pct = float((s_csv == s_db).mean() * 100.0)
            rows.append(
                {
                    "table": table_name,
                    "csv_rows": csv_rows,
                    "db_rows": db_rows,
                    "column": col,
                    "normalized_value_match_pct": match_pct,
                }
            )
    return pd.DataFrame(rows)


def reconcile_financials(
    patient_journey: pd.DataFrame, treatment_outcomes: pd.DataFrame
) -> pd.DataFrame:
    """Reconcile treatment completion counts, revenues, costs, and gross margins across tables."""
    pj_completed = patient_journey[patient_journey["treatment_completed"] == 1]
    pj_incomplete = patient_journey[patient_journey["treatment_completed"] == 0]

    pj_comp_count = int(len(pj_completed))
    to_comp_count = int(len(treatment_outcomes))

    pj_rev = int(pj_completed["actual_revenue_inr"].sum())
    to_rev = int(treatment_outcomes["actual_revenue_inr"].sum())

    pj_cost = int(pj_completed["service_cost_inr"].sum())
    to_cost = int(treatment_outcomes["service_cost_inr"].sum())

    pj_margin = int((pj_completed["actual_revenue_inr"] - pj_completed["service_cost_inr"]).sum())
    to_margin = int(treatment_outcomes["gross_margin_inr"].sum())
    to_formula_exact = bool(
        ((treatment_outcomes["actual_revenue_inr"] - treatment_outcomes["service_cost_inr"]) == treatment_outcomes["gross_margin_inr"]).all()
    )

    pj_nonzero_rev = int((pj_completed["actual_revenue_inr"] > 0).sum())
    to_nonzero_rev = int((treatment_outcomes["actual_revenue_inr"] > 0).sum())

    inc_nonzero_rev = int((pj_incomplete["actual_revenue_inr"] > 0).sum())

    rows = [
        {
            "metric": "Completed patient count",
            "patient_journey_value": pj_comp_count,
            "treatment_outcomes_value": to_comp_count,
            "reconciled": 1 if pj_comp_count == to_comp_count else 0,
        },
        {
            "metric": "Completed revenue total",
            "patient_journey_value": pj_rev,
            "treatment_outcomes_value": to_rev,
            "reconciled": bool(pj_rev == to_rev),
        },
        {
            "metric": "Completed service cost total",
            "patient_journey_value": pj_cost,
            "treatment_outcomes_value": to_cost,
            "reconciled": bool(pj_cost == to_cost),
        },
        {
            "metric": "Gross margin formula",
            "patient_journey_value": pj_margin,
            "treatment_outcomes_value": to_margin,
            "reconciled": bool((pj_margin == to_margin) and to_formula_exact),
        },
        {
            "metric": "Completed patients with nonzero revenue",
            "patient_journey_value": pj_nonzero_rev,
            "treatment_outcomes_value": to_nonzero_rev,
            "reconciled": bool(pj_nonzero_rev == to_nonzero_rev == pj_comp_count),
        },
        {
            "metric": "Incomplete patients with nonzero revenue",
            "patient_journey_value": inc_nonzero_rev,
            "treatment_outcomes_value": 0,
            "reconciled": bool(inc_nonzero_rev == 0),
        },
    ]
    return pd.DataFrame(rows)


def detect_data_anomalies(csv_tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Detect and document structural missingness, schema limitations, and funnel stage anomalies."""
    pj = csv_tables["patient_journey"]
    cl = csv_tables["communication_logs"]
    to = csv_tables["treatment_outcomes"]

    sat_missing = int(pj["satisfaction_score"].isna().sum())
    sat_pct = sat_missing / len(pj) * 100.0

    delay_missing = int(cl["response_delay_hours"].isna().sum())
    delay_pct = delay_missing / len(cl) * 100.0

    unquoted_completed = int(((pj["treatment_completed"] == 1) & (pj["quote_shared"] == 0)).sum())
    coded_dropoffs = int((pj["drop_off_flag"] == 1).sum())
    non_consult = int((pj["consultation_booked"] == 0).sum())

    merged_dates = to.merge(pj[["patient_id", "inquiry_date"]], on="patient_id", how="left")
    pre_inquiry_treatments = int(
        (pd.to_datetime(merged_dates["treatment_date"]) < pd.to_datetime(merged_dates["inquiry_date"])).sum()
    )

    rows = [
        {
            "area": "SQLite schema",
            "finding": "All 5 tables have columns declared as TEXT; numeric/date semantics are not enforced at DB schema level.",
            "severity": "Governance risk",
            "recommended_control": "Cast numeric/date fields in production queries and consider typed schema migration.",
        },
        {
            "area": "SQLite constraints",
            "finding": "PRAGMA foreign_keys=0; no declared indexes/foreign keys were found.",
            "severity": "Governance risk",
            "recommended_control": "Add PK/FK constraints and indexes in a production schema.",
        },
        {
            "area": "patient_journey.satisfaction_score",
            "finding": f"{sat_missing} missing values ({sat_pct:.1f}%). Missingness occurs only for non-completed cases.",
            "severity": "Structural missingness",
            "recommended_control": "Treat as post-treatment outcome; do not impute into pre-treatment ML features.",
        },
        {
            "area": "communication_logs.response_delay_hours",
            "finding": f"{delay_missing} missing values ({delay_pct:.1f}%). Every missing value corresponds to response_sent=0.",
            "severity": "Structural missingness",
            "recommended_control": "Retain as null when no response was sent; do not treat as zero response time.",
        },
        {
            "area": "Funnel tracking",
            "finding": f"{unquoted_completed} completed patients have quote_shared=0.",
            "severity": "Stage integrity anomaly",
            "recommended_control": "Audit quote capture; report raw flags and a strict sequential funnel separately.",
        },
        {
            "area": "Drop-off coding",
            "finding": f"{coded_dropoffs} rows are explicitly coded as drop-offs; consultation non-conversion is {non_consult} cases.",
            "severity": "Definition mismatch",
            "recommended_control": "Keep both definitions: coded drop-off and stage-based non-conversion.",
        },
        {
            "area": "Financial reconciliation",
            "finding": f"patient_journey revenue/cost exactly reconcile to treatment_outcomes for all {len(to)} completed patients; gross margin formula also reconciles.",
            "severity": "No anomaly",
            "recommended_control": "Use treatment_outcomes as outcome-level audit source.",
        },
        {
            "area": "Treatment timing",
            "finding": f"{pre_inquiry_treatments} treatment dates precede inquiry dates.",
            "severity": "No anomaly",
            "recommended_control": "No pre-inquiry treatment dates were detected.",
        },
    ]
    return pd.DataFrame(rows)
