# GitHub Upload Checklist

- [x] Review README and reports.
- [x] Keep raw patient-level CSV/SQLite files out of the public repository (`.gitignore` configured).
- [x] Commit `src/`, `sql/`, `notebooks/`, `outputs/`, `reports/`, `docs/`, `dashboard/`, `tests/`, `interview_prep/`.
- [x] Confirm `requirements.txt` installs in a clean environment.
- [x] Run notebooks from a clean environment (`scripts/build_notebooks.py` & `scripts/run_pipeline.py`).
- [x] Verify no patient identifiers are included in derived outputs.
- [x] Run automated test suite (`pytest tests/ -v` — 11/11 passed).
- [x] Add repository description: `Healthcare operations intelligence: patient funnel, provider SLA, ML risk, segmentation, and unit economics.`
