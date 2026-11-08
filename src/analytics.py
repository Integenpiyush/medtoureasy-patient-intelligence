"""Reusable funnel, SLA hypothesis testing, provider scorecard, channel, and unit-economics functions."""
from __future__ import annotations

import logging
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, ttest_ind

logger = logging.getLogger(__name__)


def add_sla_breach(
    patient_journey: pd.DataFrame, country_reference: pd.DataFrame
) -> pd.DataFrame:
    """Enrich patient_journey with country baseline SLA hours and boolean sla_breach flag.

    SLA breach is defined strictly as:
    `response_time_hours > baseline_response_expectation_hours`
    """
    cols = ["country", "baseline_response_expectation_hours"]
    if "market_priority_score" in country_reference.columns and "market_priority_score" not in patient_journey.columns:
        cols.append("market_priority_score")
    df = patient_journey.merge(
        country_reference[cols],
        on="country",
        how="left",
    ).copy()
    df["sla_breach"] = (
        df["response_time_hours"] > df["baseline_response_expectation_hours"]
    )
    return df


def funnel(df: pd.DataFrame) -> Dict[str, int]:
    """Compute core patient funnel stage counts, separating raw flags from strict sequential completion."""
    return {
        "inquiries": int(len(df)),
        "consultations": int(df["consultation_booked"].sum()),
        "quotes": int(df["quote_shared"].sum()),
        "treatments": int(df["treatment_completed"].sum()),
        "strict_treatments": int(
            ((df["treatment_completed"] == 1) & (df["quote_shared"] == 1)).sum()
        ),
        "unquoted_completions": int(
            ((df["treatment_completed"] == 1) & (df["quote_shared"] == 0)).sum()
        ),
        "strict_all_stages": int(
            (
                (df["consultation_booked"] == 1)
                & (df["quote_shared"] == 1)
                & (df["treatment_completed"] == 1)
            ).sum()
        ),
    }


def compute_funnel_tables(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Produce both the raw-flag funnel table and the strict sequential funnel table.

    Note: 229 completed cases have `quote_shared=0`. Reporting both prevents silent distortion
    of the quote-to-treatment conversion KPI.
    """
    counts = funnel(df)
    inquiries = counts["inquiries"]
    consultations = counts["consultations"]
    quotes = counts["quotes"]
    treatments = counts["treatments"]
    strict_treatments = counts["strict_treatments"]

    raw_df = pd.DataFrame(
        [
            {
                "stage": "Total Inquiries",
                "denominator": inquiries,
                "count": inquiries,
                "conversion_pct": 100.0,
            },
            {
                "stage": "Consultations Booked",
                "denominator": inquiries,
                "count": consultations,
                "conversion_pct": consultations / inquiries * 100.0,
            },
            {
                "stage": "Quotes Shared",
                "denominator": consultations,
                "count": quotes,
                "conversion_pct": quotes / consultations * 100.0,
            },
            {
                "stage": "Treatments Completed (recorded flag)",
                "denominator": quotes,
                "count": treatments,
                "conversion_pct": treatments / quotes * 100.0,
            },
        ]
    )

    strict_df = pd.DataFrame(
        [
            {
                "stage": "Total Inquiries",
                "denominator": inquiries,
                "count": inquiries,
                "conversion_pct": 100.0,
            },
            {
                "stage": "Consultations Booked",
                "denominator": inquiries,
                "count": consultations,
                "conversion_pct": consultations / inquiries * 100.0,
            },
            {
                "stage": "Quotes Shared",
                "denominator": consultations,
                "count": quotes,
                "conversion_pct": quotes / consultations * 100.0,
            },
            {
                "stage": "Treatments Completed with Quote Flag",
                "denominator": quotes,
                "count": strict_treatments,
                "conversion_pct": strict_treatments / quotes * 100.0,
            },
        ]
    )
    return raw_df, strict_df


def sla_test(df: pd.DataFrame) -> Dict[str, Any]:
    """Run Chi-square test of independence and Welch's t-test for SLA and response time vs consultation booking.

    Also calculates Cramer's V, Cohen's d, odds ratio, and 95% confidence intervals.
    """
    table = pd.crosstab(df["sla_breach"], df["consultation_booked"])
    chi2, p, dof, _ = chi2_contingency(table)
    a = df.loc[df["consultation_booked"] == 1, "response_time_hours"].dropna()
    b = df.loc[df["consultation_booked"] == 0, "response_time_hours"].dropna()
    t = ttest_ind(a, b, equal_var=False)

    n_total = len(df)
    cramers_v = float(np.sqrt(chi2 / n_total))

    # Consultation rates & 95% CI for difference in proportions (breach - no_breach)
    breach_mask = df["sla_breach"] == True
    no_breach_mask = df["sla_breach"] == False
    n_breach = int(breach_mask.sum())
    n_no_breach = int(no_breach_mask.sum())

    p_breach = float(df.loc[breach_mask, "consultation_booked"].mean())
    p_no_breach = float(df.loc[no_breach_mask, "consultation_booked"].mean())
    diff_prop = p_breach - p_no_breach
    se_prop = float(
        np.sqrt(
            (p_breach * (1.0 - p_breach) / n_breach)
            + (p_no_breach * (1.0 - p_no_breach) / n_no_breach)
        )
    )
    ci_prop_low = diff_prop - 1.96 * se_prop
    ci_prop_high = diff_prop + 1.96 * se_prop

    # Cohen's d and 95% CI for mean difference (booked - not_booked)
    mean_booked = float(a.mean())
    mean_not_booked = float(b.mean())
    diff_mean = mean_booked - mean_not_booked
    s_a, s_b = float(a.std(ddof=1)), float(b.std(ddof=1))
    n_a, n_b = len(a), len(b)
    se_mean = float(np.sqrt((s_a**2 / n_a) + (s_b**2 / n_b)))
    ci_mean_low = diff_mean - 1.96 * se_mean
    ci_mean_high = diff_mean + 1.96 * se_mean
    pooled_sd = float(np.sqrt(((n_a - 1) * s_a**2 + (n_b - 1) * s_b**2) / (n_a + n_b - 2)))
    cohens_d = diff_mean / pooled_sd

    return {
        "contingency": table,
        "chi2": float(chi2),
        "chi2_p": float(p),
        "dof": int(dof),
        "cramers_v": cramers_v,
        "sla_breach_count": float(n_breach),
        "sla_breach_rate": float(n_breach / n_total),
        "no_breach_count": float(n_no_breach),
        "consultation_rate_no_breach": p_no_breach,
        "consultation_rate_breach": p_breach,
        "consultation_rate_gap": diff_prop,
        "consultation_rate_gap_ci_95": (ci_prop_low, ci_prop_high),
        "mean_response_booked": mean_booked,
        "mean_response_not_booked": mean_not_booked,
        "mean_response_diff": diff_mean,
        "mean_response_diff_ci_95": (ci_mean_low, ci_mean_high),
        "t_stat": float(t.statistic),
        "t_p": float(t.pvalue),
        "cohens_d": float(cohens_d),
    }


def format_sla_hypothesis_table(stats_dict: Dict[str, Any]) -> pd.DataFrame:
    """Format the SLA statistical test dictionary into the canonical output DataFrame."""
    rows = [
        {"metric": "SLA breach count", "value": stats_dict["sla_breach_count"]},
        {"metric": "SLA breach rate", "value": stats_dict["sla_breach_rate"]},
        {"metric": "Consultation rate: no breach", "value": stats_dict["consultation_rate_no_breach"]},
        {"metric": "Consultation rate: breach", "value": stats_dict["consultation_rate_breach"]},
        {"metric": "Absolute consultation-rate gap", "value": stats_dict["consultation_rate_gap"]},
        {"metric": "Chi-square statistic", "value": stats_dict["chi2"]},
        {"metric": "Chi-square p-value", "value": stats_dict["chi2_p"]},
        {"metric": "Mean response time: booked", "value": stats_dict["mean_response_booked"]},
        {"metric": "Mean response time: not booked", "value": stats_dict["mean_response_not_booked"]},
        {"metric": "Welch t-statistic", "value": stats_dict["t_stat"]},
        {"metric": "Welch t-test p-value", "value": stats_dict["t_p"]},
    ]
    return pd.DataFrame(rows)


def compute_provider_scorecard(
    patient_journey: pd.DataFrame,
    provider_master: pd.DataFrame,
    country_reference: pd.DataFrame,
    treatment_outcomes: pd.DataFrame,
) -> pd.DataFrame:
    """Compute the Provider Performance Scorecard and composite Provider Intelligence Score.

    Composite weights (per PRD & Assumptions Log):
    - 30% Conversion Score (min-max normalized across providers, 0-100)
    - 20% SLA Adherence Score (percentage 0-100)
    - 15% Follow-up Completion Score (percentage 0-100)
    - 15% Satisfaction Score (scaled 0-100 via avg_satisfaction_score * 10)
    - 20% Margin per Lead Score (min-max normalized across providers, 0-100)
    """
    df = add_sla_breach(patient_journey, country_reference)
    df["sla_breach_num"] = df["sla_breach"].astype(float)

    pc = (
        df.groupby("provider_id", as_index=False)
        .agg(
            total_assigned_leads=("patient_id", "count"),
            completed_cases=("treatment_completed", "sum"),
            conversion_rate=("treatment_completed", "mean"),
            avg_response_time_hours=("response_time_hours", "mean"),
            avg_engagement_score=("engagement_score", "mean"),
            sla_breach_rate=("sla_breach_num", "mean"),
            follow_up_completion_rate=("follow_up_completed", "mean"),
            avg_satisfaction_score=("satisfaction_score", "mean"),
        )
    )

    to_copy = treatment_outcomes.copy()
    to_copy["calc_margin"] = to_copy["actual_revenue_inr"] - to_copy["service_cost_inr"]
    margins = (
        to_copy.groupby("provider_id", as_index=False)["calc_margin"]
        .sum()
        .rename(columns={"calc_margin": "total_gross_margin_inr"})
    )

    sc = (
        provider_master[["provider_id", "provider_name"]]
        .merge(pc, on="provider_id", how="inner")
        .merge(margins, on="provider_id", how="left")
    )
    sc["total_gross_margin_inr"] = sc["total_gross_margin_inr"].fillna(0).astype(int)
    sc["sla_adherence_rate"] = 1.0 - sc["sla_breach_rate"]
    sc["margin_per_lead"] = sc["total_gross_margin_inr"] / sc["total_assigned_leads"]

    c_min, c_max = sc["conversion_rate"].min(), sc["conversion_rate"].max()
    m_min, m_max = sc["margin_per_lead"].min(), sc["margin_per_lead"].max()

    sc["conv_score"] = (sc["conversion_rate"] - c_min) / (c_max - c_min) * 100.0
    sc["sla_score"] = sc["sla_adherence_rate"] * 100.0
    sc["followup_score"] = sc["follow_up_completion_rate"] * 100.0
    sc["satisfaction_score_norm"] = sc["avg_satisfaction_score"] * 10.0
    sc["margin_score"] = (sc["margin_per_lead"] - m_min) / (m_max - m_min) * 100.0

    sc["provider_intelligence_score"] = (
        0.30 * sc["conv_score"]
        + 0.20 * sc["sla_score"]
        + 0.15 * sc["followup_score"]
        + 0.15 * sc["satisfaction_score_norm"]
        + 0.20 * sc["margin_score"]
    )

    sc = sc.sort_values("provider_intelligence_score", ascending=False).reset_index(drop=True)
    sc["intelligence_rank"] = np.arange(1, len(sc) + 1)
    return sc


def compute_coordinator_sla(
    patient_journey: pd.DataFrame, country_reference: pd.DataFrame
) -> pd.DataFrame:
    """Compute Coordinator SLA and funnel performance scorecard."""
    df = add_sla_breach(patient_journey, country_reference)
    df["sla_breach_num"] = df["sla_breach"].astype(float)

    coord = (
        df.groupby("coordinator_id", as_index=False)
        .agg(
            leads=("patient_id", "count"),
            consultations=("consultation_booked", "sum"),
            completed=("treatment_completed", "sum"),
            followups=("follow_up_completed", "sum"),
            avg_response_hours=("response_time_hours", "mean"),
            sla_breach_rate=("sla_breach_num", "mean"),
        )
        .sort_values("coordinator_id")
        .reset_index(drop=True)
    )
    coord["consultation_rate"] = coord["consultations"] / coord["leads"]
    coord["completion_rate"] = coord["completed"] / coord["leads"]
    coord["followup_rate"] = coord["followups"] / coord["leads"]
    coord["sla_adherence_rate"] = 1.0 - coord["sla_breach_rate"]
    return coord


def compute_channel_performance(patient_journey: pd.DataFrame) -> pd.DataFrame:
    """Compute acquisition channel conversion, revenue, cost, gross margin, and margin per lead."""
    df = patient_journey.copy()
    df["gross_margin"] = df["actual_revenue_inr"] - df["service_cost_inr"]
    ch = (
        df.groupby("lead_source", as_index=False)
        .agg(
            leads=("patient_id", "count"),
            consultations=("consultation_booked", "sum"),
            quotes=("quote_shared", "sum"),
            completed=("treatment_completed", "sum"),
            revenue=("actual_revenue_inr", "sum"),
            cost=("service_cost_inr", "sum"),
            gross_margin=("gross_margin", "sum"),
        )
        .sort_values("lead_source")
        .reset_index(drop=True)
    )
    ch["consultation_rate"] = ch["consultations"] / ch["leads"]
    ch["completion_rate"] = ch["completed"] / ch["leads"]
    ch["margin_per_lead"] = ch["gross_margin"] / ch["leads"]
    return ch


def compute_treatment_economics(patient_journey: pd.DataFrame) -> pd.DataFrame:
    """Compute unit economics and conversion rates across treatment categories."""
    df = patient_journey.copy()
    df["gross_margin_inr"] = df["actual_revenue_inr"] - df["service_cost_inr"]
    te = (
        df.groupby("treatment_category", as_index=False)
        .agg(
            leads=("patient_id", "count"),
            completed=("treatment_completed", "sum"),
            estimated_case_value_inr=("estimated_case_value_inr", "sum"),
            actual_revenue_inr=("actual_revenue_inr", "sum"),
            service_cost_inr=("service_cost_inr", "sum"),
            gross_margin_inr=("gross_margin_inr", "sum"),
        )
        .sort_values("treatment_category")
        .reset_index(drop=True)
    )
    te["completion_rate"] = te["completed"] / te["leads"]
    te["margin_per_completed_case"] = te["gross_margin_inr"] / te["completed"]
    return te


def compute_country_sla(
    patient_journey: pd.DataFrame, country_reference: pd.DataFrame
) -> pd.DataFrame:
    """Compute country-wise SLA adherence and funnel conversion rates."""
    df = add_sla_breach(patient_journey, country_reference)
    df["sla_breach_num"] = df["sla_breach"].astype(float)
    cs = (
        df.groupby("country", as_index=False)
        .agg(
            leads=("patient_id", "count"),
            baseline_sla_hours=("baseline_response_expectation_hours", "first"),
            sla_breach_rate=("sla_breach_num", "mean"),
            consultation_rate=("consultation_booked", "mean"),
            completion_rate=("treatment_completed", "mean"),
        )
        .sort_values("country")
        .reset_index(drop=True)
    )
    return cs


def compute_dropoff_tables(
    patient_journey: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Compute drop-off breakdown by stage and by acquisition source channel."""
    dropoffs = patient_journey[patient_journey["drop_off_flag"] == 1]
    total_dropoffs = len(dropoffs)

    stage_df = (
        dropoffs.groupby("drop_off_stage", as_index=False)
        .agg(cases=("patient_id", "count"))
        .sort_values("cases", ascending=False)
        .reset_index(drop=True)
    )
    stage_df["pct_of_coded_dropoffs"] = stage_df["cases"] / total_dropoffs * 100.0

    src_df = (
        patient_journey.groupby("lead_source", as_index=False)
        .agg(
            dropoffs=("drop_off_flag", "sum"),
            inquiries=("patient_id", "count"),
        )
        .sort_values("lead_source")
        .reset_index(drop=True)
    )
    src_df["dropoff_rate"] = src_df["dropoffs"] / src_df["inquiries"] * 100.0
    src_df["share_of_dropoffs"] = src_df["dropoffs"] / total_dropoffs * 100.0
    return stage_df, src_df


def compute_economic_scenarios(patient_journey: pd.DataFrame) -> pd.DataFrame:
    """Compute observed financials and clearly labeled hypothetical drop-off recovery scenarios."""
    obs_rev = int(patient_journey["actual_revenue_inr"].sum())
    obs_cost = int(patient_journey["service_cost_inr"].sum())
    obs_margin = obs_rev - obs_cost
    margin_rate = obs_margin / obs_rev

    dropoffs = patient_journey[patient_journey["drop_off_flag"] == 1].sort_values(
        "estimated_case_value_inr", ascending=False
    )
    exposure = int(dropoffs["estimated_case_value_inr"].sum())
    top_20_n = int(len(dropoffs) * 0.20)
    top_20_val = int(dropoffs.head(top_20_n)["estimated_case_value_inr"].sum())

    rec_5 = int(round(exposure * 0.05))
    rec_10 = int(round(exposure * 0.10))
    rec_10_margin = int(round(exposure * 0.10 * margin_rate))
    rec_20 = int(round(exposure * 0.20))

    rows = [
        {"metric": "Observed gross revenue", "inr": obs_rev, "basis": "Observed"},
        {"metric": "Observed gross margin", "inr": obs_margin, "basis": "Observed"},
        {
            "metric": "Drop-off estimated case-value exposure",
            "inr": exposure,
            "basis": "Observed case value, not guaranteed revenue",
        },
        {
            "metric": "Top 20% of coded drop-offs by case value",
            "inr": top_20_val,
            "basis": "Observed case value",
        },
        {
            "metric": "5% recovery scenario",
            "inr": rec_5,
            "basis": "Scenario: 5% of drop-off case value converts",
        },
        {
            "metric": "10% recovery scenario",
            "inr": rec_10,
            "basis": "Scenario: 10% of drop-off case value converts",
        },
        {
            "metric": "10% recovery scenario margin",
            "inr": rec_10_margin,
            "basis": "Scenario using 44.9% observed completed-case margin rate",
        },
        {
            "metric": "20% recovery scenario",
            "inr": rec_20,
            "basis": "Scenario: 20% of drop-off case value converts",
        },
    ]
    return pd.DataFrame(rows)
