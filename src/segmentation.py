"""K-Means patient segmentation and persona profiling."""
from __future__ import annotations

import logging
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

SEGMENTATION_FEATURES: List[str] = [
    "intent_score",
    "response_time_hours",
    "engagement_score",
    "estimated_case_value_inr",
]


def fit_personas(
    df: pd.DataFrame,
    features: List[str] = SEGMENTATION_FEATURES,
    n_clusters: int = 3,
    random_state: int = 42,
) -> Tuple[KMeans, np.ndarray]:
    """Fit K-Means on standardized patient features and return model and cluster labels."""
    X = StandardScaler().fit_transform(df[features])
    model = KMeans(n_clusters=n_clusters, n_init=20, random_state=random_state)
    labels = model.fit_predict(X)
    return model, labels


def evaluate_cluster_counts(
    df: pd.DataFrame,
    features: List[str] = SEGMENTATION_FEATURES,
    k_range: range = range(2, 7),
    random_state: int = 42,
) -> pd.DataFrame:
    """Evaluate K-Means cluster quality across candidate k values using Inertia, Silhouette, and Davies-Bouldin."""
    X = StandardScaler().fit_transform(df[features])
    rows = []
    for k in k_range:
        km = KMeans(n_clusters=k, n_init=20, random_state=random_state)
        labels = km.fit_predict(X)
        sil = float(silhouette_score(X, labels))
        dbi = float(davies_bouldin_score(X, labels))
        rows.append(
            {
                "k": int(k),
                "inertia": float(km.inertia_),
                "silhouette_score": sil,
                "davies_bouldin_index": dbi,
            }
        )
    return pd.DataFrame(rows)


def assign_persona_names(profile_df: pd.DataFrame) -> pd.DataFrame:
    """Deterministically map cluster profiles to business-friendly persona names based on centroid characteristics.

    - Highest average case value -> 'High-Value At-Risk'
    - Highest completion / engagement among remaining -> 'High-Intent Converters'
    - Lowest engagement / completion -> 'High-Risk Disengaged'
    """
    prof = profile_df.copy()
    high_val_cluster = int(prof.loc[prof["avg_case_value_inr"].idxmax(), "cluster"])
    remaining = prof[prof["cluster"] != high_val_cluster]
    high_intent_cluster = int(remaining.loc[remaining["avg_engagement_score"].idxmax(), "cluster"])

    persona_map: Dict[int, str] = {}
    for c in prof["cluster"]:
        c_int = int(c)
        if c_int == high_val_cluster:
            persona_map[c_int] = "High-Value At-Risk"
        elif c_int == high_intent_cluster:
            persona_map[c_int] = "High-Intent Converters"
        else:
            persona_map[c_int] = "High-Risk Disengaged"

    prof["persona"] = prof["cluster"].map(persona_map)
    return prof


def build_persona_profiles(
    patient_journey: pd.DataFrame,
    features: List[str] = SEGMENTATION_FEATURES,
    n_clusters: int = 3,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, KMeans]:
    """Run K-Means segmentation, assign persona labels to patients, and generate the aggregated persona profile table."""
    model, labels = fit_personas(
        patient_journey, features=features, n_clusters=n_clusters, random_state=random_state
    )
    df = patient_journey.copy()
    df["cluster"] = labels
    df["gross_margin_inr"] = df["actual_revenue_inr"] - df["service_cost_inr"]

    prof = (
        df.groupby("cluster", as_index=False)
        .agg(
            patients=("patient_id", "count"),
            avg_intent_score=("intent_score", "mean"),
            avg_response_time_hours=("response_time_hours", "mean"),
            avg_engagement_score=("engagement_score", "mean"),
            avg_case_value_inr=("estimated_case_value_inr", "mean"),
            consultation_rate=("consultation_booked", "mean"),
            completion_rate=("treatment_completed", "mean"),
            dropoff_rate=("drop_off_flag", "mean"),
            gross_margin_inr=("gross_margin_inr", "sum"),
        )
        .sort_values("cluster")
        .reset_index(drop=True)
    )

    prof = assign_persona_names(prof)
    cluster_to_persona = dict(zip(prof["cluster"], prof["persona"]))
    df["persona"] = df["cluster"].map(cluster_to_persona)

    return prof, df, model
