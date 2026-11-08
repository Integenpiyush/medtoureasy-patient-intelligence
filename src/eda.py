"""Business-oriented Exploratory Data Analysis (EDA) and publication-quality visualizations."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)

# Set global publication-quality aesthetic
sns.set_theme(style="whitegrid", palette="deep", font_scale=1.05)
plt.rcParams["figure.dpi"] = 150
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["axes.titleweight"] = "bold"
plt.rcParams["axes.labelweight"] = "bold"


def generate_all_visualizations(
    figures_dir: Union[str, Path],
    patient_journey: pd.DataFrame,
    funnel_raw: pd.DataFrame,
    funnel_strict: pd.DataFrame,
    provider_scorecard: pd.DataFrame,
    channel_performance: pd.DataFrame,
    treatment_economics: pd.DataFrame,
    country_sla: pd.DataFrame,
    dropoff_stage: pd.DataFrame,
    ml_results: Dict[str, Any],
    persona_profiles: pd.DataFrame,
    patient_with_personas: pd.DataFrame,
) -> Dict[str, Path]:
    """Generate and save all publication-quality business charts into figures_dir."""
    out_dir = Path(figures_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    saved: Dict[str, Path] = {}

    # 1. Funnel Comparison: Raw Flags vs Strict Sequential + Drop-Off Stages
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    stages = ["Inquiries", "Consultations", "Quotes Shared", "Completed"]
    raw_counts = funnel_raw["count"].values
    strict_counts = funnel_strict["count"].values

    x = np.arange(len(stages))
    width = 0.36
    bars1 = axes[0].bar(x - width / 2, raw_counts, width, label="Recorded Flags (Raw)", color="#2b5c8f")
    bars2 = axes[0].bar(x + width / 2, strict_counts, width, label="Strict Sequential (Quoted)", color="#3690c0")
    axes[0].set_title("Patient Conversion Funnel: Raw Flags vs. Strict Sequential")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(stages)
    axes[0].set_ylabel("Number of Patients")
    axes[0].legend()
    for b in bars1:
        axes[0].annotate(
            f"{int(b.get_height()):,}",
            (b.get_x() + b.get_width() / 2, b.get_height()),
            ha="center", va="bottom", fontsize=9, fontweight="bold"
        )
    for b in bars2:
        axes[0].annotate(
            f"{int(b.get_height()):,}",
            (b.get_x() + b.get_width() / 2, b.get_height()),
            ha="center", va="bottom", fontsize=9
        )

    sns.barplot(
        data=dropoff_stage,
        y="drop_off_stage",
        x="cases",
        hue="drop_off_stage",
        palette="Reds_r",
        legend=False,
        ax=axes[1],
    )
    axes[1].set_title("Explicitly Coded Drop-Offs by Funnel Stage (n = 350)")
    axes[1].set_xlabel("Coded Drop-Off Cases")
    axes[1].set_ylabel("Drop-Off Stage")
    for i, row in dropoff_stage.iterrows():
        axes[1].text(
            row["cases"] + 1.5, i, f"{int(row['cases'])} ({row['pct_of_coded_dropoffs']:.1f}%)",
            va="center", fontsize=9, fontweight="bold"
        )
    axes[1].set_xlim(0, dropoff_stage["cases"].max() * 1.22)
    plt.tight_layout()
    p1 = out_dir / "01_funnel_and_dropoffs.png"
    fig.savefig(p1)
    plt.close(fig)
    saved["funnel_and_dropoffs"] = p1

    # 2. SLA Impact & Response Time Distribution
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    sla_labels = ["SLA Compliant\n(n = 258, 17.2%)", "SLA Breached\n(n = 1,242, 82.8%)"]
    sla_rates = [79.46, 62.72]
    colors = ["#2ca25f", "#de2d26"]
    b_sla = axes[0].bar(sla_labels, sla_rates, color=colors, width=0.5)
    axes[0].set_title("Consultation Booking Rate by SLA Adherence\n(Chi-square = 25.78, p = 3.83e-07)")
    axes[0].set_ylabel("Consultation Conversion Rate (%)")
    axes[0].set_ylim(0, 95)
    for b in b_sla:
        axes[0].annotate(
            f"{b.get_height():.1f}%",
            (b.get_x() + b.get_width() / 2, b.get_height() + 1.5),
            ha="center", fontsize=11, fontweight="bold"
        )
    axes[0].annotate(
        "-16.7 pp conversion penalty",
        xy=(1, 62.7), xytext=(0.35, 86),
        arrowprops=dict(arrowstyle="->", color="black", lw=1.5),
        fontsize=10, fontweight="bold", color="#a50f15"
    )

    pj_plot = patient_journey.copy()
    pj_plot["Consultation Status"] = pj_plot["consultation_booked"].map(
        {1: "Booked (Mean: 15.77h)", 0: "Not Booked (Mean: 19.40h)"}
    )
    sns.kdeplot(
        data=pj_plot,
        x="response_time_hours",
        hue="Consultation Status",
        fill=True,
        common_norm=False,
        palette=["#2b8cbe", "#e34a33"],
        alpha=0.4,
        ax=axes[1],
    )
    axes[1].axvline(15.77, color="#2b8cbe", linestyle="--", lw=1.5)
    axes[1].axvline(19.40, color="#e34a33", linestyle="--", lw=1.5)
    axes[1].set_title("First Response Time Distribution by Consultation Outcome\n(Welch t = -7.96, p = 4.84e-15)")
    axes[1].set_xlabel("First Response Time (Hours)")
    axes[1].set_ylabel("Density")
    plt.tight_layout()
    p2 = out_dir / "02_sla_and_response_time.png"
    fig.savefig(p2)
    plt.close(fig)
    saved["sla_and_response_time"] = p2

    # 3. Provider Intelligence Scorecard & SLA vs Conversion Quadrant
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    top_bot = pd.concat([provider_scorecard.head(5), provider_scorecard.tail(5)], ignore_index=True)
    top_bot["Group"] = ["Top 5 Benchmark"] * 5 + ["Bottom 5 Underperforming"] * 5
    sns.barplot(
        data=top_bot,
        y="provider_id",
        x="provider_intelligence_score",
        hue="Group",
        dodge=False,
        palette={"Top 5 Benchmark": "#2ca25f", "Bottom 5 Underperforming": "#de2d26"},
        ax=axes[0],
    )
    axes[0].set_title("Provider Intelligence Score: Top 5 vs. Bottom 5 Hospitals")
    axes[0].set_xlabel("Composite Provider Intelligence Score (0-100)")
    axes[0].set_ylabel("Provider ID")
    axes[0].set_xlim(0, 95)
    for i, r in top_bot.iterrows():
        axes[0].text(
            r["provider_intelligence_score"] + 1, i,
            f"{r['provider_intelligence_score']:.1f} (Conv: {r['conversion_rate']*100:.0f}%)",
            va="center", fontsize=8.5, fontweight="bold"
        )

    sc_plot = provider_scorecard.copy()
    sc_plot["conv_pct"] = sc_plot["conversion_rate"] * 100.0
    sc_plot["sla_adh_pct"] = sc_plot["sla_adherence_rate"] * 100.0
    scatter = axes[1].scatter(
        sc_plot["sla_adh_pct"],
        sc_plot["conv_pct"],
        s=sc_plot["margin_per_lead"] / 600.0,
        c=sc_plot["provider_intelligence_score"],
        cmap="viridis",
        alpha=0.85,
        edgecolors="black",
    )
    plt.colorbar(scatter, ax=axes[1], label="Intelligence Score")
    axes[1].axhline(sc_plot["conv_pct"].median(), color="gray", linestyle="--", lw=1)
    axes[1].axvline(sc_plot["sla_adh_pct"].median(), color="gray", linestyle="--", lw=1)
    for _, r in sc_plot.iloc[[0, 1, 2, -1, -2]].iterrows():
        axes[1].annotate(
            r["provider_id"],
            (r["sla_adh_pct"] + 1.0, r["conv_pct"] + 0.5),
            fontsize=8.5, fontweight="bold"
        )
    axes[1].set_title("Provider Matrix: SLA Adherence vs. Treatment Conversion\n(Bubble Size = Gross Margin per Lead)")
    axes[1].set_xlabel("SLA Adherence Rate (%)")
    axes[1].set_ylabel("Treatment Conversion Rate (%)")
    plt.tight_layout()
    p3 = out_dir / "03_provider_intelligence.png"
    fig.savefig(p3)
    plt.close(fig)
    saved["provider_intelligence"] = p3

    # 4. Channel Performance & Treatment Category Unit Economics
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.8))
    ch_sorted = channel_performance.sort_values("margin_per_lead", ascending=False)
    sns.barplot(
        data=ch_sorted,
        x="margin_per_lead",
        y="lead_source",
        hue="lead_source",
        palette="Blues_r",
        legend=False,
        ax=axes[0],
    )
    axes[0].set_title("Acquisition Channel Efficiency: Gross Margin per Lead (INR)")
    axes[0].set_xlabel("Gross Margin per Inquiry Lead (INR)")
    axes[0].set_ylabel("Acquisition Channel")
    for i, (_, r) in enumerate(ch_sorted.iterrows()):
        axes[0].text(
            r["margin_per_lead"] + 1000, i,
            f"INR {r['margin_per_lead']:,.0f} ({r['completion_rate']*100:.1f}% conv)",
            va="center", fontsize=8.5, fontweight="bold"
        )
    axes[0].set_xlim(0, ch_sorted["margin_per_lead"].max() * 1.32)

    te_sorted = treatment_economics.sort_values("gross_margin_inr", ascending=False)
    sns.barplot(
        data=te_sorted,
        x="gross_margin_inr",
        y="treatment_category",
        hue="treatment_category",
        palette="GnBu_r",
        legend=False,
        ax=axes[1],
    )
    axes[1].set_title("Total Realized Gross Margin by Treatment Category")
    axes[1].set_xlabel("Total Gross Margin (INR)")
    axes[1].set_ylabel("Treatment Category")
    for i, (_, r) in enumerate(te_sorted.iterrows()):
        axes[1].text(
            r["gross_margin_inr"] + 300000, i,
            f"INR {r['gross_margin_inr']/1e6:.1f}M (INR {r['margin_per_completed_case']/1e3:.0f}k/case)",
            va="center", fontsize=8.5, fontweight="bold"
        )
    axes[1].set_xlim(0, te_sorted["gross_margin_inr"].max() * 1.32)
    plt.tight_layout()
    p4 = out_dir / "04_channel_and_treatment_economics.png"
    fig.savefig(p4)
    plt.close(fig)
    saved["channel_and_treatment_economics"] = p4

    # 5. ML Evaluation: ROC Curve & Top 12 Feature Importances
    fig, axes = plt.subplots(1, 2, figsize=(14.5, 5.8))
    roc_data = ml_results["roc_data"]
    for name, color in [("Random Forest", "#1b7837"), ("Logistic Regression", "#2166ac")]:
        d = roc_data[name]
        axes[0].plot(d["fpr"], d["tpr"], lw=2.5, color=color, label=f"{name} (AUC = {d['auc']:.4f})")
    axes[0].plot([0, 1], [0, 1], "k--", lw=1, label="Random Baseline (AUC = 0.5000)")
    axes[0].set_title("ROC Curve: Pre-Treatment Completion Prediction (Test Split)")
    axes[0].set_xlabel("False Positive Rate (1 - Specificity)")
    axes[0].set_ylabel("True Positive Rate (Sensitivity / Recall)")
    axes[0].legend(loc="lower right")

    fi_top = ml_results["feature_importance_df"].head(12).copy()
    fi_top["clean_name"] = (
        fi_top["feature"]
        .str.replace("num__", "", regex=False)
        .str.replace("cat__", "", regex=False)
        .str.replace("_", " ", regex=False)
    )
    sns.barplot(
        data=fi_top,
        x="importance_pct",
        y="clean_name",
        hue="clean_name",
        palette="viridis",
        legend=False,
        ax=axes[1],
    )
    axes[1].set_title("Random Forest Top 12 Predictive Features (% Importance)")
    axes[1].set_xlabel("Relative Feature Importance (%)")
    axes[1].set_ylabel("Pre-Treatment Feature")
    for i, (_, r) in enumerate(fi_top.iterrows()):
        axes[1].text(r["importance_pct"] + 0.4, i, f"{r['importance_pct']:.1f}%", va="center", fontsize=8.5, fontweight="bold")
    axes[1].set_xlim(0, fi_top["importance_pct"].max() * 1.18)
    plt.tight_layout()
    p5 = out_dir / "05_ml_roc_and_feature_importance.png"
    fig.savefig(p5)
    plt.close(fig)
    saved["ml_roc_and_feature_importance"] = p5

    # 6. K-Means Patient Personas: Behavioral Separation & Economic Profile
    fig, axes = plt.subplots(1, 2, figsize=(14.5, 5.8))
    palette_personas = {
        "High-Intent Converters": "#2ca25f",
        "High-Value At-Risk": "#fe9929",
        "High-Risk Disengaged": "#de2d26",
    }
    sns.scatterplot(
        data=patient_with_personas,
        x="engagement_score",
        y="estimated_case_value_inr",
        hue="persona",
        palette=palette_personas,
        alpha=0.7,
        s=45,
        ax=axes[0],
    )
    axes[0].set_title("K-Means Patient Personas: Engagement vs. Estimated Case Value")
    axes[0].set_xlabel("Patient Engagement Score (0-100)")
    axes[0].set_ylabel("Estimated Case Value (INR)")
    axes[0].legend(title="Operational Persona")

    prof_plot = persona_profiles.copy()
    prof_plot["completion_pct"] = prof_plot["completion_rate"] * 100.0
    prof_plot["dropoff_pct"] = prof_plot["dropoff_rate"] * 100.0
    x_p = np.arange(len(prof_plot))
    w_p = 0.35
    b_c = axes[1].bar(x_p - w_p / 2, prof_plot["completion_pct"], w_p, label="Treatment Completion %", color="#2b8cbe")
    b_d = axes[1].bar(x_p + w_p / 2, prof_plot["dropoff_pct"], w_p, label="Coded Drop-Off %", color="#e34a33")
    axes[1].set_xticks(x_p)
    axes[1].set_xticklabels(prof_plot["persona"], rotation=10)
    axes[1].set_ylabel("Percentage of Cluster Patients (%)")
    axes[1].set_title("Conversion vs. Drop-Off Rate by Patient Persona")
    axes[1].legend()
    for b in list(b_c) + list(b_d):
        axes[1].annotate(
            f"{b.get_height():.1f}%",
            (b.get_x() + b.get_width() / 2, b.get_height() + 1.0),
            ha="center", fontsize=9, fontweight="bold"
        )
    axes[1].set_ylim(0, 72)
    plt.tight_layout()
    p6 = out_dir / "06_patient_personas.png"
    fig.savefig(p6)
    plt.close(fig)
    saved["patient_personas"] = p6

    # 7. Country SLA Breach Rate vs Conversion
    fig, ax = plt.subplots(figsize=(11, 5.2))
    cs_sorted = country_sla.sort_values("sla_breach_rate", ascending=False).copy()
    cs_sorted["breach_pct"] = cs_sorted["sla_breach_rate"] * 100.0
    cs_sorted["comp_pct"] = cs_sorted["completion_rate"] * 100.0
    x_c = np.arange(len(cs_sorted))
    ax.bar(x_c - 0.18, cs_sorted["breach_pct"], 0.36, label="SLA Breach Rate (%)", color="#de2d26")
    ax.bar(x_c + 0.18, cs_sorted["comp_pct"], 0.36, label="Treatment Completion Rate (%)", color="#3182bd")
    ax.set_xticks(x_c)
    ax.set_xticklabels(
        [f"{r['country']}\n({int(r['baseline_sla_hours'])}h SLA)" for _, r in cs_sorted.iterrows()],
        rotation=25, ha="right"
    )
    ax.set_ylabel("Rate (%)")
    ax.set_title("Market Comparison: Country-Specific SLA Breach Rate vs. Treatment Completion Rate")
    ax.legend()
    ax.set_ylim(0, 108)
    plt.tight_layout()
    p7 = out_dir / "07_country_sla_performance.png"
    fig.savefig(p7)
    plt.close(fig)
    saved["country_sla_performance"] = p7

    return saved
