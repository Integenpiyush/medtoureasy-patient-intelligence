"""
Generate a publication-quality, multi-page PDF Interview Preparation Guide
aligned with the user's 4 exact resume bullet points for MedTourEasy.
Uses dynamic box height calculation in Matplotlib so text never clips or overlaps.
"""

from pathlib import Path
import textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PDF = PROJECT_ROOT / "interview_prep" / "MedTourEasy_Interview_Preparation_Strategy.pdf"


# Color Palette (Executive Navy / Teal / Slate)
NAVY = "#0F172A"
TEAL = "#0F766E"
TEAL_LIGHT = "#F0FDFA"
BLUE_ACCENT = "#1D4ED8"
BLUE_LIGHT = "#EFF6FF"
AMBER_LIGHT = "#FFFBEB"
AMBER_BORDER = "#D97706"
SLATE_DARK = "#1E293B"
SLATE_MUTED = "#64748B"
BORDER_GRAY = "#CBD5E1"


def create_page(fig_size=(8.5, 11.0)):
    fig = plt.figure(figsize=fig_size, dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 130)
    ax.axis("off")
    return fig, ax


def draw_header_banner(ax, title: str, subtitle: str, page_num: int, total_pages: int = 5):
    rect = FancyBboxPatch(
        (4, 119.2), 92, 7.8,
        boxstyle="round,pad=0.3,rounding_size=0.9",
        facecolor=NAVY, edgecolor="none"
    )
    ax.add_patch(rect)
    ax.text(6.0, 124.2, title, fontsize=12.8, fontweight="bold", color="white", family="sans-serif")
    ax.text(6.0, 120.8, subtitle, fontsize=8.2, color="#CBD5E1", family="sans-serif")
    ax.text(94.2, 122.5, f"Page {page_num} of {total_pages}", fontsize=8.5, fontweight="bold",
            color="#38BDF8", ha="right", family="sans-serif")

    # Footer (well separated left & right)
    ax.plot([4, 96], [4.6, 4.6], color=BORDER_GRAY, linewidth=0.7)
    ax.text(4.0, 2.5, "MedTourEasy Patient Intelligence  |  Interview Defense Playbook",
            fontsize=7.3, color=SLATE_MUTED, family="sans-serif")
    ax.text(96.0, 2.5, "github.com/Integenpiyush/medtoureasy-patient-intelligence",
            fontsize=7.3, color=TEAL, ha="right", family="sans-serif")


def measure_and_wrap(text_lines, width=114, line_height=1.52, para_gap=0.32):
    """Pre-calculates wrapped lines and exact vertical height required."""
    rendered = []
    total_h = 0.0
    for item in text_lines:
        if item == "":
            rendered.append(("GAP", "", False))
            total_h += line_height * 0.45
            continue
        is_bold = item.startswith("[BOLD]")
        clean_item = item.replace("[BOLD]", "")
        is_bullet = clean_item.startswith("• ") or clean_item.startswith("- ")
        sub_indent = "   " if is_bullet else ""
        wrapped = textwrap.wrap(clean_item, width=width, subsequent_indent=sub_indent)
        for idx, wline in enumerate(wrapped):
            rendered.append(("LINE", wline, is_bold and idx == 0))
            total_h += line_height
        total_h += para_gap
    return rendered, total_h


def draw_section_card(ax, top_y, title, text_lines, bg, border,
                      width_chars=115, fontsize=7.8, line_height=1.50,
                      para_gap=0.28, header_bar=False):
    """
    Draws a rounded card starting at `top_y` whose height automatically fits `text_lines`.
    Returns the new `top_y` below the card.
    """
    rendered, text_h = measure_and_wrap(text_lines, width=width_chars,
                                         line_height=line_height, para_gap=para_gap)
    header_h = 3.6 if header_bar else 2.9
    pad_top = 1.1
    pad_bottom = 1.2
    box_h = header_h + pad_top + text_h + pad_bottom
    bottom_y = top_y - box_h

    card = FancyBboxPatch(
        (4, bottom_y), 92, box_h,
        boxstyle="round,pad=0.15,rounding_size=0.7",
        facecolor=bg, edgecolor=border, linewidth=1.0
    )
    ax.add_patch(card)

    if header_bar:
        hbar = FancyBboxPatch(
            (4, top_y - header_h), 92, header_h,
            boxstyle="round,pad=0.1,rounding_size=0.6",
            facecolor=border, edgecolor="none"
        )
        ax.add_patch(hbar)
        ax.text(5.8, top_y - header_h + 1.1, title, fontsize=8.8,
                fontweight="bold", color="white", family="sans-serif")
    else:
        ax.text(5.8, top_y - 2.1, title, fontsize=8.6,
                fontweight="bold", color=border, family="sans-serif")

    cur_y = top_y - header_h - pad_top
    for kind, wline, is_bold in rendered:
        if kind == "GAP":
            cur_y -= line_height * 0.45
            continue
        ax.text(
            5.8, cur_y, wline,
            fontsize=fontsize,
            color=SLATE_DARK,
            fontweight="bold" if is_bold else "normal",
            family="sans-serif",
            va="top"
        )
        cur_y -= line_height
    return bottom_y - 1.5


def build_page_1(pdf, total_pages=5):
    fig, ax = create_page()
    draw_header_banner(
        ax,
        "MEDTOUREASY — 3-TIER INTERVIEW PREPARATION STRATEGY",
        "Resume-Aligned Scripts (30-40 Sec | 2-3 Min | 10-15 Min Deep-Dive) & Audited Metric Cheat Sheet",
        page_num=1, total_pages=total_pages
    )

    cur_y = 117.2
    resume_lines = [
        "[BOLD]Data Science & Analytics Intern | MedTourEasy  (May'26 – July'26)",
        "• [Bullet 1] Engineered Python/SQL pipeline across 1,500 patient journeys and 5 datasets for funnel and provider analytics.",
        "• [Bullet 2] Quantified a 16.7 pp SLA conversion gap (62.7% vs. 79.5%) using Chi-square statistical testing (p < 0.001).",
        "• [Bullet 3] Built Logistic Regression and Random Forest classifiers, achieving 0.8695 ROC-AUC with leakage-aware features.",
        "• [Bullet 4] Segmented 1,500 patients into 3 personas using K-Means on intent, engagement, response time, and case value.",
    ]
    cur_y = draw_section_card(
        ax, cur_y,
        "YOUR EXACT RESUME ENTRY (SOURCE OF TRUTH FOR INTERVIEWERS)",
        resume_lines, bg=BLUE_LIGHT, border=BLUE_ACCENT,
        width_chars=116, fontsize=7.9, line_height=1.52, para_gap=0.25
    )

    cheat_lines = [
        "• Cohort & 5 Datasets: 1,500 inquiries | 554 completed (36.93%) | 350 explicit drop-offs (23.33%) | 596 stagnant open leads. Tables: patient_journey (1,500), provider_master (30), communication_logs (6,025), treatment_outcomes (554), country_reference (12). Zero PK/FK orphans.",
        "• Audited Financials: INR 248,325,245 Realized Revenue (INR 448.2k/case) | INR 136,810,889 Cost | INR 111,514,356 Gross Margin (44.91% margin; INR 201.3k/case).",
        "• Critical Funnel Anomaly: 229 of 554 completed patients (41.34%) had quote_shared=0, inflating naive quote-to-treatment conversion to 98.75% (554/561) vs. True Strict Sequential conversion of 57.93% (325/561).",
        "• SLA Proof: 82.80% breached country SLA (1,242/1,500). Consult booking: 79.46% (SLA Met) vs 62.72% (Breached) -> -16.74 pp (Chi2=25.78, p=3.83e-7). Welch t-test: 15.77h (booked) vs 19.40h (unbooked), p=4.84e-15.",
        "• ML & Personas: 72h cutoff -> Random Forest 0.8695 ROC-AUC vs Logistic Regression 0.8193. K-Means (k=3) isolates 426 High-Value At-Risk leads (INR 716.8k avg value, 31.9% conv). 10% drop-off recovery = INR 16.65M rev / INR 7.48M margin.",
    ]
    cur_y = draw_section_card(
        ax, cur_y,
        "MASTER NUMBERS CHEAT SHEET (MEMORIZE COLD BEFORE ENTERING THE INTERVIEW)",
        cheat_lines, bg=TEAL_LIGHT, border=TEAL,
        width_chars=116, fontsize=7.65, line_height=1.46, para_gap=0.22
    )

    pitch1_lines = [
        "[BOLD]When to use: Opening intro, 'Walk me through a project on your resume', or Recruiter/HM screen (~105 words).",
        "\"At MedTourEasy, I built an end-to-end patient conversion and provider intelligence system across 1,500 international medical tourism inquiries and 5 relational datasets representing INR 248.3 million in completed treatment revenue and INR 111.5 million in gross margin.",
        "First, I engineered a Python and SQL data quality pipeline that uncovered 229 off-system treatment completions that were artificially inflating quote conversion from 57.9% to 98.8%. Second, using Chi-square testing against country-specific SLA benchmarks, I proved that 82.8% of inquiries breached SLA, causing a 16.7 percentage point drop in consultation booking (62.7% vs. 79.5%, p < 0.001).",
        "Finally, I built a leakage-free Random Forest model achieving 0.8695 ROC-AUC at a 72-hour prediction cutoff and combined it with K-Means clustering (k=3) to isolate 426 High-Value At-Risk patients averaging INR 716.8k per case—creating a targeted routing playbook to recover an estimated INR 7.5 million in gross margin at a 10% recovery rate.\"",
    ]
    cur_y = draw_section_card(
        ax, cur_y,
        "STRATEGY 1: THE 30–40 SECOND ELEVATOR PITCH (WORD-FOR-WORD SCRIPT)",
        pitch1_lines, bg="white", border=NAVY,
        width_chars=115, fontsize=7.9, line_height=1.50, para_gap=0.30, header_bar=True
    )

    pacing_lines = [
        "• [00–10 sec] Business Scale Hook: Anchor the scale immediately (1,500 inquiries, 5 datasets, INR 248.3M revenue, INR 111.5M margin).",
        "• [10–25 sec] Engineering + Statistical Rigor: Hit the 229 unquoted completions anomaly (57.9% vs 98.8%) and the -16.7 pp SLA Chi-square result (p < 0.001).",
        "• [25–40 sec] ML + Personas + ROI: Pair the 0.8695 ROC-AUC model (72h cutoff) with the 426 High-Value At-Risk K-Means persona and INR 7.5M margin recovery.",
        "• Strategic Pause at 0:40: Stop right after 'INR 7.5 million in gross margin.' This invites the interviewer to ask about your 72h leakage guardrails or the 229 unquoted completions.",
    ]
    draw_section_card(
        ax, cur_y,
        "DELIVERY CUES & WHY THIS 30–40 SECOND SCRIPT WORKS",
        pacing_lines, bg=AMBER_LIGHT, border=AMBER_BORDER,
        width_chars=116, fontsize=7.65, line_height=1.45, para_gap=0.20
    )

    pdf.savefig(fig)
    plt.close(fig)


def build_page_2(pdf, total_pages=5):
    fig, ax = create_page()
    draw_header_banner(
        ax,
        "STRATEGY 2: THE 2–3 MINUTE STRUCTURED WALKTHROUGH",
        "Hiring Manager & Technical Screen Script — Mapped 1:1 to Your 4 Resume Bullets (~400 Words)",
        page_num=2, total_pages=total_pages
    )

    cur_y = 117.2
    blocks = [
        (
            "PART 1 (0:00 – 0:45) | BUSINESS PROBLEM & PYTHON/SQL PIPELINE (RESUME BULLET 1)",
            BLUE_LIGHT, BLUE_ACCENT,
            [
                "\"MedTourEasy coordinates cross-border medical travel across 12 source countries, 8 high-acuity specialties like Oncology and Cardiac Surgery, and 30 partner hospitals. Out of 1,500 patient inquiries, 554 completed treatment (36.93%), generating INR 248.3M in revenue and INR 111.5M in gross margin (44.91% margin rate). However, 946 patients failed to convert—including 350 explicitly coded drop-offs representing INR 166.5M in lost case-value exposure.",
                "To diagnose where and why patients leaked, I built a modular Python and SQLite pipeline across 5 tables: patient_journey (1,500 rows), provider_master (30 hospitals), communication_logs (6,025 interactions), treatment_outcomes (554 completed cases), and country_reference (12 countries). Because the SQLite tables stored numbers as TEXT without primary or foreign key enforcement, I wrote automated schema and reconciliation tests. That audit caught a critical funnel flaw: 229 of the 554 completed patients (41.3%) had quote_shared = 0, making naive quote-to-treatment conversion look like 98.75% (554/561). Filtering to strict sequential progression (325/561) revealed the true 57.93% quote conversion rate.\""
            ]
        ),
        (
            "PART 2 (0:45 – 1:25) | COUNTRY-SPECIFIC SLA BREACH & STATISTICAL PROOF (RESUME BULLET 2)",
            TEAL_LIGHT, TEAL,
            [
                "\"Second, rather than using a single global response threshold, I joined every inquiry to its country-specific SLA expectation in country_reference (6 hours for Nigeria/Nepal/Sri Lanka, 8 hours for India/UAE/Malaysia, and 12 hours for Bangladesh/Kenya/Oman/Thailand). I discovered that 82.80% of inquiries (1,242 of 1,500) breached SLA, averaging ~17 hours.",
                "Using a Chi-square test of independence, I proved that inquiries meeting SLA booked consultations at 79.46% (205/258) versus 62.72% (779/1,242) when SLA was breached—a 16.74 percentage point drop (Chi-square = 25.78, p = 3.83e-7, Cramer's V = 0.131). I also verified this continuously with Welch's two-sample t-test: booked consultations averaged 15.77 hours response time versus 19.40 hours for non-booked leads (-3.63 hours, t = -7.96, p = 4.84e-15).\""
            ]
        ),
        (
            "PART 3 (1:25 – 2:10) | LEAKAGE-AWARE ML CLASSIFICATION — 0.8695 ROC-AUC (RESUME BULLET 3)",
            BLUE_LIGHT, BLUE_ACCENT,
            [
                "\"Third, to predict treatment_completed early enough for coordinators to intervene, I established a strict 72-hour post-inquiry prediction cutoff. I excluded all post-treatment financials, satisfaction_score (which is structurally null for all 946 non-completed patients), and downstream stage flags (consultation_booked, quote_shared, drop_off_flag), and aggregated communication_logs strictly within <= 72 hours of inquiry.",
                "Using an 80/20 stratified split (1,200 train / 300 test) inside a scikit-learn ColumnTransformer pipeline, I benchmarked balanced Logistic Regression (0.8193 ROC-AUC) against a regularized Random Forest classifier (0.8695 ROC-AUC, 0.7723 Precision, 0.7358 F1). Top drivers were engagement_score (29.6% importance), estimated_case_value_inr (13.0%), intent_score (7.5%), and response_time_hours (7.4%). Because a missed patient costs INR 201k in margin while a follow-up call costs pennies, I tuned the probability threshold from 0.50 to 0.40, boosting Recall from 70.3% to 78.4%.\""
            ]
        ),
        (
            "PART 4 (2:10 – 2:50) | K-MEANS PERSONAS & INR 7.5M MARGIN RECOVERY PLAYBOOK (RESUME BULLET 4)",
            TEAL_LIGHT, TEAL,
            [
                "\"Finally, a risk probability alone doesn't separate a low-intent inquiry from an expensive surgical candidate. I standardized intent_score, engagement_score, response_time_hours, and estimated_case_value_inr with StandardScaler and applied K-Means (k=3) to segment patients into: (1) High-Intent Converters (38.1% of cohort, 60.2% completion), (2) High-Risk Disengaged (33.5%, 14.7% completion, slowest 19.8h response), and (3) High-Value At-Risk (28.4%, 426 patients)—who carry the highest average case value at INR 716.8k (2.2x other clusters) but convert at only 31.9%.",
                "Combining our ML risk scores with K-Means personas and our composite Provider Scorecard, we built an operational routing playbook: escalating High-Value At-Risk patients in the 0.35–0.65 probability band to top-performing hospitals (PVD-020, PVD-008) and senior coordinators (COORD-06). Recovering just 10% of the 350 explicit drop-offs (~35 cases) yields INR 16.65M in incremental revenue and INR 7.48M in gross margin.\""
            ]
        ),
    ]

    for title, bg, border, lines in blocks:
        cur_y = draw_section_card(
            ax, cur_y, title, lines, bg=bg, border=border,
            width_chars=116, fontsize=7.85, line_height=1.50, para_gap=0.28
        )

    pdf.savefig(fig)
    plt.close(fig)


def build_page_3(pdf, total_pages=5):
    fig, ax = create_page()
    draw_header_banner(
        ax,
        "STRATEGY 3: 10–15 MIN DEEP-DIVE (PART A: BULLETS 1 & 2)",
        "Minutes 0:00 to 8:00 — Architecture, Data Quality, Dual Funnel, Provider Scorecard & SLA Testing",
        page_num=3, total_pages=total_pages
    )

    cur_y = 117.2
    min0_2 = [
        "• Business Scope: Cross-border medical travel across 12 source countries (India, Bangladesh, UAE, Nigeria, Kenya, Thailand, etc.), 7 acquisition channels, 8 specialties (Cardiac, Oncology, Organ Transplant, Ortho, Fertility, etc.), 30 hospitals, and 10 coordinators.",
        "• Verified Unit Economics: 1,500 Inquiries -> 554 Completed Treatments (36.93%) | Revenue: INR 248,325,245 (INR 448.2k/case) | Service Cost: INR 136,810,889 (INR 247.0k/case) | Realized Gross Margin: INR 111,514,356 (44.91% margin; INR 201.3k/case).",
        "• Non-Completed Breakdown (946 patients / 63.07%): 350 explicitly coded drop-offs (drop_off_flag=1, INR 166.51M case-value exposure) + 596 stagnant open inquiries (212 stuck at Inquiry, 264 at Consultation, 120 at Quote Shared).",
        "• Production Repository: Modular Python (src/data_quality.py, analytics.py, modeling.py, segmentation.py, eda.py) + 11 SQL queries (sql/medtoureasy_analysis.sql) + 6-page Streamlit app (dashboard/app.py) + 11 automated pytest tests.",
    ]
    cur_y = draw_section_card(
        ax, cur_y,
        "MINUTES 0:00 – 2:00 | BUSINESS CONTEXT, UNIT ECONOMICS & REPOSITORY ARCHITECTURE",
        min0_2, bg="white", border=NAVY,
        width_chars=116, fontsize=7.65, line_height=1.45, para_gap=0.20
    )

    min2_5 = [
        "[BOLD]1. Schema & Relational Reconciliation Across 5 Datasets (CSV + SQLite mte_patient_intelligence.db):",
        "• Validated 0 PK duplicates/nulls and 0 FK orphans across patient_journey (1,500), provider_master (30), communication_logs (6,025), treatment_outcomes (554), and country_reference (12). Hardened SQLite TEXT columns via explicit CAST(... AS INTEGER/REAL).",
        "• Structural Missingness Classification: satisfaction_score has 946/1,500 nulls (exact 946 non-completed rows); drop_off_stage has 1,150/1,500 nulls (exact non-dropped rows); response_delay_hours has 1,413/6,025 nulls (exact unresponded logs, 23.45%).",
        "[BOLD]2. The '229 Unquoted Completions' Discovery (Why Naive Funnel Math Fails):",
        "• Raw counts: 1,500 Inquiries -> 984 Consultations (65.60%) -> 561 Quotes Shared (57.01% of consults) -> 554 Completions (36.93%).",
        "• Naive division (554/561) implies a 98.75% quote conversion rate! Auditing stage flags proved 229 of 554 completed patients (41.34%) had consultation_booked=1 and treatment_completed=1, but quote_shared=0 (direct package/bypass bookings). Separating Strict Sequential Completions (325/561) reveals the true 57.93% quote-to-treatment conversion rate (21.67% strict overall).",
        "[BOLD]3. Composite Provider Intelligence Scorecard (0–100 Weighted Index across 30 Hospitals, ~50 leads/provider):",
        "• Formula: 30% Norm Conversion + 20% Norm SLA Adherence + 15% Norm Follow-up + 15% Norm Satisfaction + 20% Norm Margin/Lead.",
        "• Top Performers: PVD-020 (Score 80.78 | 52.73% conv | 5.85h resp | 72.73% SLA | INR 85.2k margin/lead) & PVD-008 (Score 71.77 | 48.21% conv | highest margin/lead at INR 111.7k). Bottleneck: PVD-007 (52.0% conv, 18.0% SLA) vs Low: PVD-023 (26.9% conv, 0% SLA).",
    ]
    cur_y = draw_section_card(
        ax, cur_y,
        "MINUTES 2:00 – 5:00 | BULLET 1 DEFENSE: DATA QUALITY, DUAL FUNNEL & PROVIDER SCORECARD",
        min2_5, bg=BLUE_LIGHT, border=BLUE_ACCENT,
        width_chars=116, fontsize=7.6, line_height=1.43, para_gap=0.18
    )

    min5_8 = [
        "[BOLD]1. Country-Specific SLA Benchmark (Why a Global Cutoff Is Flawed):",
        "• Joined patient_journey.response_time_hours against country_reference.baseline_response_expectation_hours: 6h SLA (Nigeria, Nepal, Sri Lanka), 8h SLA (India, Malaysia, Philippines, Tanzania, UAE), and 12h SLA (Bangladesh, Kenya, Oman, Thailand).",
        "• System-Wide SLA Failure: 1,242 / 1,500 inquiries (82.80%) breached SLA; only 258 (17.20%) met SLA. Worst breaches occur in 6h-SLA markets (Nigeria 97.6%, Sri Lanka 97.2%, Nepal 94.7%) because coordinator shifts run on an unsegmented ~17h cycle.",
        "[BOLD]2. Dual Hypothesis Testing Framework (Categorical Chi-Square + Continuous Welch's t-Test):",
        "• Pearson's Chi-Square Test (2x2 Table): SLA Met booked at 79.46% (205/258) vs. SLA Breached at 62.72% (779/1,242) -> -16.74 pp gap (95% CI: [-22.39 pp, -11.09 pp]), Chi2 = 25.7784 (dof=1), p = 3.83e-7 (p < 0.001), Cramer's V = 0.1311, Odds Ratio = 0.435.",
        "• Downstream Ripple: SLA compliance also lifts Quote Sharing by +11.47 pp (46.90% vs 35.43%) and Completion by +11.57 pp (46.51% vs 34.94%).",
        "• Welch's Two-Sample t-Test: Booked consultations (n=984) averaged 15.77h (SD 7.91h) vs Non-booked (n=516) at 19.40h (SD 8.63h) -> Delta = -3.63h, Welch t = -7.9569, p = 4.84e-15, Cohen's d = -0.431. Proposed stratified randomized A/B test (<4h routing) for causal proof.",
    ]
    draw_section_card(
        ax, cur_y,
        "MINUTES 5:00 – 8:00 | BULLET 2 DEFENSE: SLA BREACH ANALYSIS & STATISTICAL TESTING",
        min5_8, bg=TEAL_LIGHT, border=TEAL,
        width_chars=116, fontsize=7.6, line_height=1.43, para_gap=0.18
    )

    pdf.savefig(fig)
    plt.close(fig)


def build_page_4(pdf, total_pages=5):
    fig, ax = create_page()
    draw_header_banner(
        ax,
        "STRATEGY 3: 10–15 MIN DEEP-DIVE (PART B: BULLETS 3 & 4)",
        "Minutes 8:00 to 15:00 — Leakage-Aware ML (0.8695 AUC), Threshold Tuning, K-Means Personas & ROI",
        page_num=4, total_pages=total_pages
    )

    cur_y = 117.2
    min8_12 = [
        "[BOLD]1. Prediction Timestamp & Three-Layer Leakage Prevention Architecture (72-Hour Post-Inquiry Cutoff):",
        "• Layer 1 (Post-Treatment Financials & Outcomes): Excluded actual_revenue_inr, service_cost_inr, gross_margin_inr, and all treatment_outcomes fields (length_of_stay_days, complication_flag).",
        "• Layer 2 (Structural Null Proxy — satisfaction_score): satisfaction_score is missing for 100% of non-completed rows (946/946) and 0% of completed rows (0/554). Including it with median imputation lets a tree split on the imputed value for ~1.00 fake AUC. Excluded!",
        "• Layer 3 (Downstream Funnel Flags & Future Comm Logs): Excluded consultation_booked, quote_shared, follow_up_completed, current_stage, drop_off_flag, drop_off_stage, reason_for_drop_off. Filtered communication_logs strictly to 0 <= t_comm - t_inquiry <= 72 hours (engineering early_interactions, early_response_rate, early_avg_response_delay, early_followup_completed).",
        "[BOLD]2. Pipeline Engineering & Model Comparison (Stratified 80/20 Split: 1,200 Train / 300 Test, random_state=42):",
        "• Built scikit-learn ColumnTransformer + Pipeline (SimpleImputer + StandardScaler on 19 numeric features; SimpleImputer + OneHotEncoder on 6 categorical features) fit strictly on X_train.",
        "• Logistic Regression (C=1.0, class_weight='balanced'): ROC-AUC = 0.8193 | Precision = 0.6187 | Recall = 0.7748 | F1 = 0.6880 (TN=136, FP=53, FN=25, TP=86). Calibrated Odds Ratios: engagement_score OR=3.15, intent_score OR=1.63, response_time OR=0.70, case_value OR=0.63.",
        "• Random Forest (n_estimators=500, min_samples_leaf=3, max_features=0.7, class_weight='balanced'): ROC-AUC = 0.8695 (+5.02 pp lift) | Accuracy = 81.33% | Precision = 0.7723 | Recall = 0.7027 | F1 = 0.7358 (TN=166, FP=23, FN=33, TP=78).",
        "• Top 5 RF Features (Gini): engagement_score (29.63%), estimated_case_value_inr (12.96%), intent_score (7.53%), response_time_hours (7.42%), early_avg_response_delay (4.70%).",
        "[BOLD]3. Cost-Sensitive Threshold Optimization (Why 0.50 Is Suboptimal for Medical Tourism):",
        "• False Negative loses ~INR 201,289 in gross margin; False Positive costs ~15 mins of coordinator time. Lowering threshold from 0.50 to 0.40 boosts Recall from 70.27% to 78.38% (+8.11 pp, catching 9 extra completers in test set) with Precision at 67.97% and F1 at 0.7280.",
    ]
    cur_y = draw_section_card(
        ax, cur_y,
        "MINUTES 8:00 – 12:00 | BULLET 3 DEFENSE: LEAKAGE-AWARE ML PIPELINE (0.8695 ROC-AUC)",
        min8_12, bg=BLUE_LIGHT, border=BLUE_ACCENT,
        width_chars=116, fontsize=7.6, line_height=1.43, para_gap=0.18
    )

    min12_15 = [
        "[BOLD]1. Unsupervised K-Means Clustering Methodology & Validation:",
        "• Features: intent_score (0–100), engagement_score (0–100), response_time_hours (1–46h), estimated_case_value_inr (INR 75k–1.5M).",
        "• Why StandardScaler Is Mandatory: Without z-score standardization, estimated_case_value_inr (~10^5–10^6 INR) dominates >99.99% of Euclidean distance. Evaluated k in {2..6} via Inertia, Silhouette Score, and Davies-Bouldin Index (k=2 Sil=0.264, k=3 Sil=0.233 / DBI=1.448). Picked k=3 because k=2 failed to isolate high-value surgical patients.",
        "[BOLD]2. The 3 Patient Personas & Operational Routing Playbook:",
        "• High-Intent Converters (Cluster 1 — 571 patients / 38.1%): Intent 75.3 | Engagement 69.7 | Resp 15.0h | Case Value INR 327.0k -> 82.0% consult, 60.2% completion, 10.2% drop-off, INR 52.20M gross margin. Action: Fast-track quotes & automated visa/travel checklists.",
        "• High-Value At-Risk (Cluster 2 — 426 patients / 28.4%): Highest Case Value at INR 716.8k (2.19x Cluster 1!) | Intent 63.1 | Engagement 55.5 | Resp 16.4h -> 67.8% consult, only 31.9% completion, 24.6% drop-off, INR 46.58M margin. Action: #1 Priority! Route leads in 0.35–0.65 ML prob band to top hospitals (PVD-020, PVD-008) & senior coordinators (COORD-06, COORD-03) with itemized financial counseling.",
        "• High-Risk Disengaged (Cluster 0 — 503 patients / 33.5%): Intent 45.6 | Engagement 32.1 | Slowest Resp 19.8h | Case Value INR 402.1k -> 45.1% consult, 14.7% completion, 37.2% drop-off, INR 12.74M margin. Action: Automated <1h WhatsApp/Chatbot intake before human triage.",
        "[BOLD]3. Scenario-Based Financial Opportunity (350 Explicit Drop-Offs = INR 166.51M Case-Value Exposure):",
        "• 5% Recovery (~18 cases): INR 8.33M Rev / INR 3.74M Gross Margin | 10% Recovery (Base Target — ~35 cases): INR 16.65M Rev / INR 7.48M Gross Margin | 15% Recovery (~53 cases): INR 24.98M Rev / INR 11.22M Margin | 20% Recovery (~70 cases): INR 33.30M Rev / INR 14.96M Margin.",
    ]
    draw_section_card(
        ax, cur_y,
        "MINUTES 12:00 – 15:00 | BULLET 4 DEFENSE: K-MEANS PERSONAS & FINANCIAL SCENARIOS",
        min12_15, bg=TEAL_LIGHT, border=TEAL,
        width_chars=116, fontsize=7.6, line_height=1.43, para_gap=0.18
    )

    pdf.savefig(fig)
    plt.close(fig)


def build_page_5(pdf, total_pages=5):
    fig, ax = create_page()
    draw_header_banner(
        ax,
        "BULLET-BY-BULLET INTERVIEWER CROSS-EXAMINATION GUIDE",
        "The Exact Tough Follow-Up Questions Interviewers Will Ask When Reading Each Line of Your Resume",
        page_num=5, total_pages=total_pages
    )

    cur_y = 117.2
    q_blocks = [
        (
            "CROSS-EXAMINATION ON BULLET 1 (PYTHON/SQL PIPELINE, 5 DATASETS, FUNNEL & PROVIDERS)",
            BLUE_LIGHT, BLUE_ACCENT,
            [
                "[BOLD]Q1: 'What was the hardest data quality bug you caught across the 5 datasets?'",
                "• Answer: Two critical issues: First, 229 out of 554 completed patients (41.34%) had consultation_booked=1 and treatment_completed=1 but quote_shared=0. Naive funnel math (554/561) reported a 98.75% quote conversion rate; isolating strict sequential completions (325/561) revealed the true 57.93% rate. Second, SQLite stored numeric columns as TEXT without PK/FK constraints, requiring explicit CAST statements across all 11 SQL queries.",
                "[BOLD]Q2: 'Why didn't you rank hospitals purely by conversion rate or total revenue?'",
                "• Answer: Single metrics hide operational bottlenecks. For instance, PVD-007 achieved 52.0% conversion and INR 110.6k margin/lead, but had an 18.0% SLA adherence rate (10.17h response). Conversely, PVD-020 delivered 52.7% conversion with 72.7% SLA adherence (5.85h response). Our 0–100 Provider Intelligence Score weights Conversion (30%), SLA Adherence (20%), Margin/Lead (20%), Follow-up (15%), and Satisfaction (15%)."
            ]
        ),
        (
            "CROSS-EXAMINATION ON BULLET 2 (16.7 PP SLA CONVERSION GAP & CHI-SQUARE P < 0.001)",
            TEAL_LIGHT, TEAL,
            [
                "[BOLD]Q3: 'Why did you use Chi-square instead of just comparing averages, and what were the exact numbers?'",
                "• Answer: Because both sla_breach (0/1) and consultation_booked (0/1) are binary categorical outcomes, Pearson's Chi-square test of independence is the exact statistical test. SLA-compliant leads converted at 79.46% (205/258) vs. 62.72% (779/1,242) for breached leads (-16.74 pp, 95% CI [-22.39 pp, -11.09 pp], Chi2 = 25.78, p = 3.83e-7). To ensure the binary cutoff wasn't hiding continuous behavior, I also ran Welch's t-test on raw response_time_hours (15.77h booked vs 19.40h unbooked, t = -7.96, p = 4.84e-15).",
                "[BOLD]Q4: 'Does your Chi-square test prove that faster response time CAUSES higher conversion?'",
                "• Answer: No—in observational CRM data, response delay can correlate with medical complexity or arrival time. I framed it as a strong observational association and proposed a stratified randomized A/B test (randomizing leads within country x specialty strata to a <4h rapid-response desk vs standard queue) to measure causal lift."
            ]
        ),
        (
            "CROSS-EXAMINATION ON BULLET 3 (LOGISTIC REGRESSION & RANDOM FOREST — 0.8695 ROC-AUC)",
            BLUE_LIGHT, BLUE_ACCENT,
            [
                "[BOLD]Q5: 'Walk me through every feature you dropped to prevent data leakage and why.'",
                "• Answer: I set the prediction point at 72 hours post-inquiry. I dropped: (1) post-treatment financials (actual_revenue_inr, service_cost_inr, gross_margin_inr), (2) satisfaction_score—which is missing for all 946 non-completed rows and populated for all 554 completed rows, so imputing it creates a 100% target leak, (3) downstream funnel flags (consultation_booked, quote_shared, drop_off_flag, current_stage), and (4) communication_logs occurring >72 hours after inquiry.",
                "[BOLD]Q6: 'Why did you keep Logistic Regression if Random Forest achieved 0.8695 vs 0.8193 ROC-AUC?'",
                "• Answer: Random Forest is our production ranking engine (+5.02 pp AUC lift because it captures non-linear interactions like engagement x response_time and case_value x complexity), while Logistic Regression gives calibrated directional Odds Ratios for clinical leadership (e.g., +1 SD in engagement increases completion odds by 3.15x, while +1 SD in case value reduces odds by 0.63x due to price sensitivity)."
            ]
        ),
        (
            "CROSS-EXAMINATION ON BULLET 4 (K-MEANS SEGMENTATION INTO 3 PATIENT PERSONAS)",
            TEAL_LIGHT, TEAL,
            [
                "[BOLD]Q7: 'Why did you standardize features before K-Means, and why pick k=3 when k=2 had a slightly higher Silhouette score?'",
                "• Answer: K-Means minimizes isotropic Euclidean distance; without StandardScaler, estimated_case_value_inr (ranging up to INR 1.5M) overwhelms 0–100 scores by 10,000x. Across k in {2..6}, k=2 (Silhouette 0.264) only split high vs low engagement. Selecting k=3 (Silhouette 0.233, Davies-Bouldin 1.448) isolated the 426 High-Value At-Risk patients (INR 716.8k avg case value, 31.9% conversion)—the single most actionable segment for senior coordinator escalation.",
                "[BOLD]Q8: 'How do your ML model and K-Means personas work together in production?'",
                "• Answer: They form a 2x2 routing matrix: ML predicts conversion likelihood at 72h, while K-Means identifies economic value and behavioral posture. A High-Value At-Risk patient in the 0.35–0.65 ML probability band gets immediate senior coordinator & top-hospital escalation."
            ]
        ),
    ]

    for title, bg, border, lines in q_blocks:
        cur_y = draw_section_card(
            ax, cur_y, title, lines, bg=bg, border=border,
            width_chars=116, fontsize=7.65, line_height=1.44, para_gap=0.20
        )

    pdf.savefig(fig)
    plt.close(fig)


def main():
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(OUTPUT_PDF) as pdf:
        build_page_1(pdf, total_pages=5)
        build_page_2(pdf, total_pages=5)
        build_page_3(pdf, total_pages=5)
        build_page_4(pdf, total_pages=5)
        build_page_5(pdf, total_pages=5)
    print(f"Successfully generated PDF at: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
