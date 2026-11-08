"""MedTourEasy Patient Conversion & Provider Performance Intelligence Dashboard.

Interactive Streamlit dashboard covering:
1. Executive Overview
2. Funnel Analysis & SLA Statistical Intelligence
3. Provider & Coordinator Intelligence
4. Channel & Treatment Unit Economics
5. ML Risk Intelligence (Logistic Regression vs Random Forest)
6. K-Means Patient Personas & Recovery Economics
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(
    page_title="MedTourEasy Patient Intelligence",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_dashboard_data():
    """Load precomputed outputs and raw datasets (if available) for interactive filtering."""
    out_dir = ROOT / "outputs"
    data_dir = ROOT / "data"

    outputs = {
        "funnel_raw": pd.read_csv(out_dir / "funnel_raw_flags.csv"),
        "funnel_strict": pd.read_csv(out_dir / "funnel_strict_sequential.csv"),
        "dropoff_stage": pd.read_csv(out_dir / "dropoff_stage.csv"),
        "dropoff_source": pd.read_csv(out_dir / "dropoff_source.csv"),
        "sla_test": pd.read_csv(out_dir / "sla_hypothesis_test.csv"),
        "provider_scorecard": pd.read_csv(out_dir / "provider_scorecard.csv"),
        "coordinator_sla": pd.read_csv(out_dir / "coordinator_sla.csv"),
        "channel_performance": pd.read_csv(out_dir / "channel_performance.csv"),
        "treatment_economics": pd.read_csv(out_dir / "treatment_economics.csv"),
        "country_sla": pd.read_csv(out_dir / "country_sla.csv"),
        "model_metrics": pd.read_csv(out_dir / "model_metrics.csv"),
        "model_thresholds": pd.read_csv(out_dir / "model_thresholds.csv"),
        "rf_fi": pd.read_csv(out_dir / "random_forest_feature_importance.csv"),
        "persona_profiles": pd.read_csv(out_dir / "persona_profiles.csv"),
        "economic_scenarios": pd.read_csv(out_dir / "economic_impact_scenarios.csv"),
        "dq_profile": pd.read_csv(out_dir / "data_quality_profile.csv"),
        "fin_recon": pd.read_csv(out_dir / "financial_reconciliation.csv"),
        "anomalies": pd.read_csv(out_dir / "data_anomalies.csv"),
    }

    pj_path = data_dir / "patient_journey.csv"
    if pj_path.exists():
        from src.analytics import add_sla_breach
        from src.data_quality import load_csvs
        from src.modeling import prepare_modeling_dataset, train_and_evaluate_models
        from src.segmentation import build_persona_profiles

        csvs = load_csvs(data_dir)
        pj = add_sla_breach(csvs["patient_journey"], csvs["country_reference"])
        _, pj_personas, _ = build_persona_profiles(pj)
        ml_df = prepare_modeling_dataset(
            csvs["patient_journey"],
            csvs["provider_master"],
            csvs["communication_logs"],
            csvs["country_reference"],
        )
        ml_live = train_and_evaluate_models(ml_df)
        outputs["patient_journey"] = pj_personas
        outputs["ml_live"] = ml_live
    else:
        outputs["patient_journey"] = None
        outputs["ml_live"] = None

    return outputs


def render_dashboard():
    data = load_dashboard_data()
    pj = data["patient_journey"]

    st.sidebar.title("🏥 MedTourEasy Intelligence")
    st.sidebar.caption("International Patient Conversion, SLA & ML Risk System")

    page = st.sidebar.radio(
        "Navigation",
        [
            "1. Executive Overview",
            "2. Funnel & SLA Analytics",
            "3. Provider & Coordinator Intelligence",
            "4. Channel & Treatment Economics",
            "5. ML Completion Risk Intelligence",
            "6. Patient Personas & Scenarios",
        ],
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Audited Governance Highlights")
    st.sidebar.info(
        "- **Base Population:** 1,500 patient journeys\n"
        "- **Funnel Anomaly:** 229 completed cases lack `quote_shared=1` (strict sequential conversion: **57.9%** vs 98.8% raw flag)\n"
        "- **SLA Association:** 82.8% breach rate; **62.7% vs 79.5%** consultation booking ($p = 3.83 \\times 10^{-7}$)\n"
        "- **Leakage Guardrail:** Post-treatment fields & >72h logs excluded from ML"
    )

    if page == "1. Executive Overview":
        st.title("📊 Executive Overview: Patient Journey & Unit Economics")
        st.markdown(
            "End-to-end operational performance across **1,500 international patient inquiries**, **30 partner hospitals**, **15 care coordinators**, and **12 source countries**."
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Patient Inquiries", "1,500", "12 Source Markets")
        c2.metric("Consultations Booked", "984 (65.6%)", "-516 Unbooked Inquiries")
        c3.metric("Quotes Shared", "561 (57.0%)", "Of 984 Consultations")
        c4.metric("Treatments Completed", "554 (36.9%)", "325 Strict Sequential (57.9%)")

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Observed Gross Revenue", "₹248.33M", "554 Completed Cases")
        c6.metric("Observed Gross Margin", "₹111.51M", "44.91% Margin Rate")
        c7.metric("SLA Breach Rate", "82.8%", "-16.7 pp Consultation Gap", delta_color="inverse")
        c8.metric("Coded Drop-off Exposure", "₹166.51M", "350 Coded Drop-offs")

        st.markdown("---")
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Funnel Reconciliation: Raw Flags vs. Strict Sequential")
            f_comp = pd.DataFrame(
                {
                    "Stage": ["Total Inquiries", "Consultations Booked", "Quotes Shared", "Treatments Completed"],
                    "Raw Flag Count": data["funnel_raw"]["count"],
                    "Strict Sequential Count": data["funnel_strict"]["count"],
                }
            )
            fig_f = go.Figure()
            fig_f.add_trace(
                go.Bar(
                    name="Raw Stage Flags",
                    x=f_comp["Stage"],
                    y=f_comp["Raw Flag Count"],
                    text=f_comp["Raw Flag Count"],
                    textposition="auto",
                    marker_color="#1f77b4",
                )
            )
            fig_f.add_trace(
                go.Bar(
                    name="Strict Sequential (Quoted)",
                    x=f_comp["Stage"],
                    y=f_comp["Strict Sequential Count"],
                    text=f_comp["Strict Sequential Count"],
                    textposition="auto",
                    marker_color="#2ca02c",
                )
            )
            fig_f.update_layout(barmode="group", height=380, yaxis_title="Patient Count")
            st.plotly_chart(fig_f, use_container_width=True)

        with col_right:
            st.subheader("Financial Reconciliation & Economic Scenarios")
            econ = data["economic_scenarios"].copy()
            econ["INR (Millions)"] = (econ["inr"] / 1e6).round(2)
            st.dataframe(
                econ[["metric", "INR (Millions)", "basis"]],
                use_container_width=True,
                hide_index=True,
            )
            st.caption(
                "Note: Recovery numbers are planning scenarios (5%, 10%, 20% of drop-off case value exposure), not realized revenue or causal forecasts."
            )

        st.subheader("Data Governance & Anomaly Audit Summary")
        st.dataframe(data["anomalies"], use_container_width=True, hide_index=True)

    elif page == "2. Funnel & SLA Analytics":
        st.title("⏳ Patient Funnel Leakage & Response-Time SLA Analysis")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Explicitly Coded Drop-Offs by Funnel Stage (n = 350)")
            ds = data["dropoff_stage"]
            fig_ds = px.bar(
                ds,
                x="cases",
                y="drop_off_stage",
                orientation="h",
                color="pct_of_coded_dropoffs",
                text=ds.apply(lambda r: f"{int(r['cases'])} ({r['pct_of_coded_dropoffs']:.1f}%)", axis=1),
                color_continuous_scale="Reds",
                labels={"cases": "Drop-off Count", "drop_off_stage": "Funnel Stage"},
            )
            fig_ds.update_layout(yaxis={"categoryorder": "total ascending"}, height=370)
            st.plotly_chart(fig_ds, use_container_width=True)

        with col2:
            st.subheader("Drop-Off Rate by Acquisition Channel")
            dsrc = data["dropoff_source"].sort_values("dropoff_rate", ascending=False)
            fig_dsrc = px.bar(
                dsrc,
                x="lead_source",
                y="dropoff_rate",
                color="dropoff_rate",
                text=dsrc["dropoff_rate"].map(lambda v: f"{v:.1f}%"),
                color_continuous_scale="OrRd",
                labels={"lead_source": "Lead Source", "dropoff_rate": "Coded Drop-Off Rate (%)"},
            )
            fig_dsrc.update_layout(height=370)
            st.plotly_chart(fig_dsrc, use_container_width=True)

        st.markdown("---")
        st.subheader("Statistical Hypothesis Testing: SLA Adherence vs. Consultation Booking")
        s_col1, s_col2 = st.columns([1.2, 1])
        with s_col1:
            st.dataframe(data["sla_test"], use_container_width=True, hide_index=True)
            st.markdown(
                """
                **Statistical Defense & Interpretation:**
                - **Chi-Square Test:** $\\chi^2 = 25.78, p = 3.83 \\times 10^{-7}$ (Cramér's $V = 0.131$). Patients whose first response met their country SLA booked consultations at **79.46%**, compared to **62.72%** for SLA-breached cases (**-16.74 pp gap**).
                - **Welch's t-Test:** $t = -7.96, p = 4.84 \\times 10^{-15}$ (Cohen's $d = -0.431$). Consultation-booked patients experienced a mean first response time of **15.77h** vs. **19.40h** for non-booked patients.
                - **Observational Caveat:** This establishes strong statistical association, not causation. Unobserved confounders (e.g., clinical complexity, timezone overlap) may influence both response speed and booking propensity.
                """
            )
        with s_col2:
            csla = data["country_sla"].sort_values("sla_breach_rate", ascending=False)
            fig_csla = px.scatter(
                csla,
                x="sla_breach_rate",
                y="consultation_rate",
                size="leads",
                color="baseline_sla_hours",
                hover_name="country",
                text="country",
                labels={
                    "sla_breach_rate": "Country SLA Breach Rate",
                    "consultation_rate": "Consultation Booking Rate",
                    "baseline_sla_hours": "Baseline SLA (h)",
                },
                title="Country SLA Breach Rate vs. Consultation Rate",
            )
            fig_csla.update_traces(textposition="top center")
            st.plotly_chart(fig_csla, use_container_width=True)

    elif page == "3. Provider & Coordinator Intelligence":
        st.title("🏥 Provider & Coordinator Performance Scorecards")
        sc = data["provider_scorecard"]

        st.subheader("Composite Provider Intelligence Leaderboard (30 Partner Hospitals)")
        st.caption(
            "Composite Formula: 30% Conversion Score + 20% SLA Adherence + 15% Follow-up Completion + 15% Satisfaction + 20% Margin per Lead"
        )

        min_leads = st.slider("Minimum Assigned Patient Leads Filter", min_value=30, max_value=60, value=38)
        sc_filt = sc[sc["total_assigned_leads"] >= min_leads].copy()

        fig_p = px.scatter(
            sc_filt,
            x="sla_adherence_rate",
            y="conversion_rate",
            size="margin_per_lead",
            color="provider_intelligence_score",
            hover_name="provider_name",
            text="provider_id",
            color_continuous_scale="Viridis",
            labels={
                "sla_adherence_rate": "SLA Adherence Rate",
                "conversion_rate": "Treatment Conversion Rate",
                "provider_intelligence_score": "Intelligence Score",
            },
            title="Provider Performance Matrix: SLA Adherence vs. Conversion (Size = Margin/Lead)",
        )
        fig_p.update_traces(textposition="top center")
        st.plotly_chart(fig_p, use_container_width=True)

        st.dataframe(
            sc_filt[
                [
                    "intelligence_rank",
                    "provider_id",
                    "provider_name",
                    "total_assigned_leads",
                    "completed_cases",
                    "conversion_rate",
                    "avg_response_time_hours",
                    "sla_adherence_rate",
                    "follow_up_completion_rate",
                    "avg_satisfaction_score",
                    "total_gross_margin_inr",
                    "margin_per_lead",
                    "provider_intelligence_score",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")
        st.subheader("Care Coordinator SLA & Conversion Benchmarking (15 Coordinators)")
        coord = data["coordinator_sla"].sort_values("completion_rate", ascending=False)
        st.dataframe(coord, use_container_width=True, hide_index=True)

    elif page == "4. Channel & Treatment Economics":
        st.title("💰 Acquisition Channel & Treatment Category Unit Economics")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Acquisition Channel Performance")
            ch = data["channel_performance"].sort_values("margin_per_lead", ascending=False)
            fig_ch = px.bar(
                ch,
                x="lead_source",
                y="margin_per_lead",
                color="completion_rate",
                text=ch["margin_per_lead"].map(lambda v: f"₹{v:,.0f}"),
                color_continuous_scale="Blues",
                labels={"lead_source": "Channel", "margin_per_lead": "Gross Margin per Lead (₹)"},
                title="Gross Margin per Lead & Completion Rate by Channel",
            )
            st.plotly_chart(fig_ch, use_container_width=True)
            st.dataframe(ch, use_container_width=True, hide_index=True)

        with col2:
            st.subheader("Treatment Category Unit Economics")
            te = data["treatment_economics"].sort_values("gross_margin_inr", ascending=False)
            fig_te = px.bar(
                te,
                x="gross_margin_inr",
                y="treatment_category",
                orientation="h",
                color="margin_per_completed_case",
                text=te["gross_margin_inr"].map(lambda v: f"₹{v/1e6:.2f}M"),
                color_continuous_scale="Tealgrn",
                labels={
                    "gross_margin_inr": "Total Gross Margin (₹)",
                    "treatment_category": "Specialty",
                },
                title="Total Gross Margin & Margin per Completed Case by Specialty",
            )
            fig_te.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_te, use_container_width=True)
            st.dataframe(te, use_container_width=True, hide_index=True)

    elif page == "5. ML Completion Risk Intelligence":
        st.title("🤖 Supervised ML: Pre-Treatment Completion Prediction")
        st.markdown(
            """
            **Target:** `treatment_completed` (Binary classification on 80/20 stratified train-test split, $N_{\\text{train}}=1,200, N_{\\text{test}}=300$).  
            **Leakage Prevention:** Strictly restricted to features known at inquiry + early communication activity within the **first 72 hours**. Post-treatment satisfaction, actual revenue/cost, and stage/drop-off flags are excluded.
            """
        )

        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.subheader("Model Evaluation Summary (Threshold = 0.50)")
            st.dataframe(data["model_metrics"], use_container_width=True, hide_index=True)

            st.subheader("Operational Threshold Tuning (Random Forest)")
            selected_t = st.select_slider(
                "Select Classification Probability Threshold",
                options=[0.3, 0.4, 0.5, 0.6],
                value=0.4,
            )
            t_df = data["model_thresholds"]
            st.dataframe(t_df, use_container_width=True, hide_index=True)
            row_t = t_df[t_df["threshold"] == selected_t].iloc[0]
            st.success(
                f"At threshold **{selected_t:.2f}**: Precision = **{row_t['precision']*100:.1f}%**, "
                f"Recall = **{row_t['recall']*100:.1f}%**, F1 = **{row_t['f1']:.4f}** "
                f"(TP={int(row_t['tp'])}, FP={int(row_t['fp'])}, FN={int(row_t['fn'])}, TN={int(row_t['tn'])})"
            )

        with m_col2:
            st.subheader("Top 15 Random Forest Predictive Features")
            fi = data["rf_fi"].head(15).copy()
            fi["Feature"] = (
                fi["feature"]
                .str.replace("num__", "", regex=False)
                .str.replace("cat__", "", regex=False)
            )
            fig_fi = px.bar(
                fi,
                x="importance_pct",
                y="Feature",
                orientation="h",
                color="importance_pct",
                text=fi["importance_pct"].map(lambda v: f"{v:.1f}%"),
                color_continuous_scale="Viridis",
                labels={"importance_pct": "Importance (%)"},
            )
            fig_fi.update_layout(yaxis={"categoryorder": "total ascending"}, height=480)
            st.plotly_chart(fig_fi, use_container_width=True)

        if data["ml_live"] is not None:
            st.markdown("---")
            st.subheader("ROC Curve & Test-Set Predicted Probability Distribution")
            rc1, rc2 = st.columns(2)
            with rc1:
                roc_d = data["ml_live"]["roc_data"]
                fig_roc = go.Figure()
                for name, col in [("Random Forest", "#2ca02c"), ("Logistic Regression", "#1f77b4")]:
                    fig_roc.add_trace(
                        go.Scatter(
                            x=roc_d[name]["fpr"],
                            y=roc_d[name]["tpr"],
                            mode="lines",
                            name=f"{name} (AUC={roc_d[name]['auc']:.4f})",
                            line=dict(color=col, width=3),
                        )
                    )
                fig_roc.add_trace(
                    go.Scatter(
                        x=[0, 1], y=[0, 1], mode="lines", name="Random (0.50)", line=dict(dash="dash", color="gray")
                    )
                )
                fig_roc.update_layout(
                    title="ROC Curve Comparison (Test Set, n=300)",
                    xaxis_title="False Positive Rate",
                    yaxis_title="True Positive Rate (Recall)",
                )
                st.plotly_chart(fig_roc, use_container_width=True)
            with rc2:
                rf_probs = data["ml_live"]["test_probs"]["Random Forest"]
                y_test = data["ml_live"]["y_test"]
                prob_df = pd.DataFrame(
                    {
                        "Predicted Completion Probability": rf_probs,
                        "Actual Outcome": y_test.map({1: "Completed Treatment", 0: "Did Not Complete"}),
                    }
                )
                fig_dist = px.histogram(
                    prob_df,
                    x="Predicted Completion Probability",
                    color="Actual Outcome",
                    barmode="overlay",
                    nbins=25,
                    opacity=0.7,
                    title="Random Forest Predicted Probability Distribution by Outcome",
                )
                fig_dist.add_vline(x=selected_t, line_dash="dash", line_color="red", annotation_text=f"Threshold {selected_t}")
                st.plotly_chart(fig_dist, use_container_width=True)
        elif (ROOT / "outputs" / "figures" / "05_ml_roc_and_feature_importance.png").exists():
            st.markdown("---")
            st.subheader("ROC Curve & Top Predictive Drivers (Precomputed Test Evaluation)")
            st.image(
                str(ROOT / "outputs" / "figures" / "05_ml_roc_and_feature_importance.png"),
                use_container_width=True,
            )

    elif page == "6. Patient Personas & Scenarios":
        st.title("👥 K-Means Patient Personas & Actionable Workflows")
        prof = data["persona_profiles"]

        st.subheader("Cluster Persona Profiles (k = 3 Standardized K-Means)")
        st.dataframe(prof, use_container_width=True, hide_index=True)

        p_col1, p_col2 = st.columns(2)
        with p_col1:
            fig_p1 = px.bar(
                prof,
                x="persona",
                y=["consultation_rate", "completion_rate", "dropoff_rate"],
                barmode="group",
                title="Funnel Conversion & Drop-Off Rates by Patient Persona",
                labels={"value": "Rate (0-1)", "persona": "Persona"},
            )
            st.plotly_chart(fig_p1, use_container_width=True)

        with p_col2:
            if pj is not None:
                fig_p2 = px.scatter(
                    pj,
                    x="engagement_score",
                    y="estimated_case_value_inr",
                    color="persona",
                    hover_data=["patient_id", "country", "treatment_category", "intent_score"],
                    title="Patient Personas: Engagement Score vs. Estimated Case Value (INR)",
                )
                st.plotly_chart(fig_p2, use_container_width=True)
            else:
                fig_p2 = px.bar(
                    prof,
                    x="persona",
                    y="gross_margin_inr",
                    color="persona",
                    text=prof["gross_margin_inr"].map(lambda v: f"₹{v/1e6:.2f}M"),
                    title="Realized Gross Margin by Patient Persona (INR)",
                    labels={"gross_margin_inr": "Gross Margin (₹)", "persona": "Persona"},
                )
                st.plotly_chart(fig_p2, use_container_width=True)

        st.markdown(
            """
            ### Operational Playbook by Persona
            1. **High-Intent Converters (571 patients | 60.2% completion | ₹52.2M margin):**  
               *Profile:* Highest intent (75.3) & engagement (69.7), fastest response (15.0h).  
               *Action:* Protect SLA, fast-track consultation scheduling and quote generation, avoid coordinator bottlenecks.
            2. **High-Value At-Risk (426 patients | 31.9% completion | ₹716.8k avg case value | ₹46.6M margin):**  
               *Profile:* Complex, high-ticket procedures (Oncology, Transplant, Neurology) with moderate engagement (55.5) and 24.6% coded drop-off rate.  
               *Action:* Route immediately to senior care coordinators and top-tier hospitals (`PVD-020`, `PVD-008`, `PVD-015`); provide transparent itemized quotes and medical-visa assistance.
            3. **High-Risk Disengaged (503 patients | 14.7% completion | 37.2% drop-off | 19.8h avg response):**  
               *Profile:* Lowest intent (45.6) & engagement (32.1), slowest initial response.  
               *Action:* Trigger automated WhatsApp/Chatbot re-engagement within <4 hours; address cost and language barriers early before spending heavy clinical desk time.
            """
        )


if __name__ == "__main__":
    render_dashboard()
