"""Data loading and governance helpers for the MedTourEasy project."""
from pathlib import Path
import sqlite3
import pandas as pd

TABLES = ["patient_journey","provider_master","communication_logs","treatment_outcomes","country_reference"]

def load_csvs(data_dir):
    data_dir = Path(data_dir)
    return {t: pd.read_csv(data_dir / f"{t}.csv") for t in TABLES}

def load_sqlite(db_path):
    conn = sqlite3.connect(db_path)
    try:
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name", conn
        )["name"].tolist()
        return {t: pd.read_sql_query(f'SELECT * FROM "{t}"', conn) for t in tables}
    finally:
        conn.close()

def profile(df):
    out = pd.DataFrame({
        "column": df.columns,
        "dtype": df.dtypes.astype(str).values,
        "null_count": df.isna().sum().values,
    })
    out["null_pct"] = out["null_count"] / len(df) * 100
    out["unique_count"] = [df[c].nunique(dropna=True) for c in df.columns]
    return out
