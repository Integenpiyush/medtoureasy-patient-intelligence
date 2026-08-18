"""Entry point for reproducible project execution.

This script intentionally keeps raw data outside version control. Run it after
placing the six supplied source files under data/.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
print("MedTourEasy pipeline root:", ROOT)
print("Use the notebooks for the full analytical workflow.")
print("SQL layer:", ROOT / "sql" / "medtoureasy_analysis.sql")
print("Outputs:", ROOT / "outputs")
