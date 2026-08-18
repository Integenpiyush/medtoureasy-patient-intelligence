"""Reusable funnel, SLA, provider and unit-economics functions."""
import pandas as pd
from scipy.stats import chi2_contingency, ttest_ind

def add_sla_breach(patient_journey, country_reference):
    df = patient_journey.merge(
        country_reference[["country","baseline_response_expectation_hours"]],
        on="country", how="left"
    ).copy()
    df["sla_breach"] = (
        df["response_time_hours"] > df["baseline_response_expectation_hours"]
    )
    return df

def funnel(df):
    return {
        "inquiries": len(df),
        "consultations": int(df["consultation_booked"].sum()),
        "quotes": int(df["quote_shared"].sum()),
        "treatments": int(df["treatment_completed"].sum()),
        "strict_treatments": int(
            ((df["treatment_completed"] == 1) & (df["quote_shared"] == 1)).sum()
        ),
    }

def sla_test(df):
    table = pd.crosstab(df["sla_breach"], df["consultation_booked"])
    chi2, p, dof, _ = chi2_contingency(table)
    a = df.loc[df["consultation_booked"] == 1, "response_time_hours"].dropna()
    b = df.loc[df["consultation_booked"] == 0, "response_time_hours"].dropna()
    t = ttest_ind(a, b, equal_var=False)
    return {"contingency": table, "chi2": chi2, "chi2_p": p, "t_stat": t.statistic, "t_p": t.pvalue}
