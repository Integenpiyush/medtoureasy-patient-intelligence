"""Treatment-completion predictive modeling pipeline with strict leakage prevention."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logger = logging.getLogger(__name__)

# Strict pre-treatment feature set (available at or within 72h after inquiry).
# Explicitly excludes post-treatment and target-leaking variables:
# - actual_revenue_inr, service_cost_inr, gross_margin_inr
# - satisfaction_score (only recorded post-treatment)
# - consultation_booked, quote_shared, follow_up_completed, current_stage, drop_off_flag, drop_off_stage, reason_for_drop_off
# - communication logs occurring >72 hours after inquiry_date
NUMERIC_FEATURES: List[str] = [
    "intent_score",
    "response_time_hours",
    "engagement_score",
    "estimated_case_value_inr",
    "baseline_response_expectation_hours",
    "market_priority_score",
    "avg_first_response_hours",
    "historical_consultation_conversion_rate",
    "historical_treatment_conversion_rate",
    "follow_up_completion_rate",
    "satisfaction_index",
    "early_interactions",
    "early_response_rate",
    "early_avg_response_delay",
    "early_followup_completed",
]

CATEGORICAL_FEATURES: List[str] = [
    "country",
    "age_group",
    "gender",
    "treatment_category",
    "lead_source",
    "budget_band",
    "medical_urgency",
]

FORBIDDEN_LEAKAGE_FEATURES: List[str] = [
    "actual_revenue_inr",
    "service_cost_inr",
    "gross_margin_inr",
    "satisfaction_score",
    "treatment_date",
    "length_of_stay_days",
    "readmission_within_30d",
    "follow_up_rating",
    "current_stage",
    "drop_off_flag",
    "drop_off_stage",
    "reason_for_drop_off",
]


def build_logistic(
    numeric_features: List[str] = NUMERIC_FEATURES,
    categorical_features: List[str] = CATEGORICAL_FEATURES,
) -> Pipeline:
    """Build a scikit-learn Pipeline with median/mode imputation, scaling, OHE, and balanced Logistic Regression."""
    num = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    cat = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("ohe", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    pre = ColumnTransformer(
        [("num", num, numeric_features), ("cat", cat, categorical_features)]
    )
    return Pipeline(
        [
            ("pre", pre),
            ("model", LogisticRegression(max_iter=2000, class_weight="balanced")),
        ]
    )


def build_random_forest(
    numeric_features: List[str] = NUMERIC_FEATURES,
    categorical_features: List[str] = CATEGORICAL_FEATURES,
) -> Pipeline:
    """Build a scikit-learn Pipeline with median/mode imputation, OHE, and balanced Random Forest."""
    num = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    cat = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("ohe", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    pre = ColumnTransformer(
        [("num", num, numeric_features), ("cat", cat, categorical_features)]
    )
    model = RandomForestClassifier(
        n_estimators=500,
        max_depth=None,
        min_samples_leaf=3,
        max_features=0.7,
        class_weight="balanced",
        random_state=42,
        n_jobs=2,
    )
    return Pipeline([("pre", pre), ("model", model)])


def prepare_modeling_dataset(
    patient_journey: pd.DataFrame,
    provider_master: pd.DataFrame,
    communication_logs: pd.DataFrame,
    country_reference: pd.DataFrame,
    cutoff_hours: float = 72.0,
) -> pd.DataFrame:
    """Engineer strictly pre-cutoff features (default: first 72 hours after inquiry).

    Prevents target leakage by filtering communication_logs to `0 <= hours_since_inquiry <= cutoff_hours`
    and excluding all post-treatment or outcome variables.
    """
    cl = communication_logs.merge(
        patient_journey[["patient_id", "inquiry_date"]],
        on="patient_id",
        how="left",
    )
    ts = pd.to_datetime(cl["timestamp"])
    inq = pd.to_datetime(cl["inquiry_date"])
    cl["hours_since_inquiry"] = (ts - inq).dt.total_seconds() / 3600.0

    early = cl[
        (cl["hours_since_inquiry"] >= 0.0) & (cl["hours_since_inquiry"] <= cutoff_hours)
    ].copy()
    early["followup_completed_num"] = (early["follow_up_status"] == "Completed").astype(int)

    early_agg = (
        early.groupby("patient_id", as_index=False)
        .agg(
            early_interactions=("communication_id", "count"),
            early_response_rate=("response_sent", "mean"),
            early_avg_response_delay=("response_delay_hours", "mean"),
            early_followup_completed=("followup_completed_num", "sum"),
        )
    )

    pm_cols = [
        "provider_id",
        "avg_first_response_hours",
        "historical_consultation_conversion_rate",
        "historical_treatment_conversion_rate",
        "follow_up_completion_rate",
        "satisfaction_index",
    ]
    cr_cols = [
        "country",
        "baseline_response_expectation_hours",
        "market_priority_score",
    ]

    df = (
        patient_journey.merge(provider_master[pm_cols], on="provider_id", how="left")
        .merge(country_reference[cr_cols], on="country", how="left")
        .merge(early_agg, on="patient_id", how="left")
    )

    df["early_interactions"] = df["early_interactions"].fillna(0.0)
    df["early_response_rate"] = df["early_response_rate"].fillna(0.0)
    df["early_followup_completed"] = df["early_followup_completed"].fillna(0.0)
    # Note: early_avg_response_delay is intentionally kept as NaN when no response occurred
    # in the first 72h so that the pipeline's SimpleImputer(strategy="median") imputes it cleanly
    # within each training fold without data leakage.

    return df


def train_and_evaluate_models(
    df: pd.DataFrame,
    numeric_features: List[str] = NUMERIC_FEATURES,
    categorical_features: List[str] = CATEGORICAL_FEATURES,
    target_col: str = "treatment_completed",
    test_size: float = 0.20,
    random_state: int = 42,
) -> Dict[str, Any]:
    """Train Logistic Regression and Random Forest on an 80/20 stratified split and compute full evaluation artifacts."""
    # Verify no forbidden leakage columns are in the feature lists
    requested_features = set(numeric_features + categorical_features)
    leaked = requested_features.intersection(set(FORBIDDEN_LEAKAGE_FEATURES))
    if leaked:
        raise ValueError(f"Data leakage detected! Forbidden features in model input: {leaked}")

    X = df[numeric_features + categorical_features]
    y = df[target_col].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state
    )

    lr_pipe = build_logistic(numeric_features, categorical_features)
    rf_pipe = build_random_forest(numeric_features, categorical_features)

    lr_pipe.fit(X_train, y_train)
    rf_pipe.fit(X_train, y_train)

    metrics_rows = []
    roc_data = {}
    probs_dict = {}

    for model_name, pipe in [
        ("Logistic Regression", lr_pipe),
        ("Random Forest", rf_pipe),
    ]:
        probs = pipe.predict_proba(X_test)[:, 1]
        preds = (probs >= 0.50).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_test, preds).ravel()
        auc = float(roc_auc_score(y_test, probs))
        prec = float(precision_score(y_test, preds))
        rec = float(recall_score(y_test, preds))
        f1 = float(f1_score(y_test, preds))

        metrics_rows.append(
            {
                "model": model_name,
                "roc_auc": auc,
                "precision": prec,
                "recall": rec,
                "f1": f1,
                "tn": int(tn),
                "fp": int(fp),
                "fn": int(fn),
                "tp": int(tp),
            }
        )
        fpr, tpr, thresh = roc_curve(y_test, probs)
        roc_data[model_name] = {"fpr": fpr, "tpr": tpr, "thresholds": thresh, "auc": auc}
        probs_dict[model_name] = probs

    metrics_df = pd.DataFrame(metrics_rows)

    # Threshold trade-off analysis for Random Forest across [0.3, 0.4, 0.5, 0.6]
    rf_probs = probs_dict["Random Forest"]
    thresh_rows = []
    for t in [0.3, 0.4, 0.5, 0.6]:
        t_preds = (rf_probs >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_test, t_preds).ravel()
        thresh_rows.append(
            {
                "threshold": float(t),
                "precision": float(precision_score(y_test, t_preds)),
                "recall": float(recall_score(y_test, t_preds)),
                "f1": float(f1_score(y_test, t_preds)),
                "tn": int(tn),
                "fp": int(fp),
                "fn": int(fn),
                "tp": int(tp),
            }
        )
    thresholds_df = pd.DataFrame(thresh_rows)

    # Feature importances from Random Forest
    feature_names = rf_pipe.named_steps["pre"].get_feature_names_out()
    importances = rf_pipe.named_steps["model"].feature_importances_
    fi_df = (
        pd.DataFrame(
            {
                "feature": feature_names,
                "importance": importances,
                "importance_pct": importances * 100.0,
            }
        )
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )

    # Logistic Regression coefficients for interpretability
    lr_feature_names = lr_pipe.named_steps["pre"].get_feature_names_out()
    lr_coefs = lr_pipe.named_steps["model"].coef_[0]
    lr_coef_df = (
        pd.DataFrame(
            {
                "feature": lr_feature_names,
                "coefficient": lr_coefs,
                "odds_ratio": np.exp(lr_coefs),
                "abs_coefficient": np.abs(lr_coefs),
            }
        )
        .sort_values("abs_coefficient", ascending=False)
        .reset_index(drop=True)
    )

    return {
        "logistic_pipeline": lr_pipe,
        "rf_pipeline": rf_pipe,
        "metrics_df": metrics_df,
        "thresholds_df": thresholds_df,
        "feature_importance_df": fi_df,
        "logistic_coefficients_df": lr_coef_df,
        "roc_data": roc_data,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "test_probs": probs_dict,
    }
