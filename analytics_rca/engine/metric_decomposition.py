import numpy as np
import pandas as pd
import itertools


def safe_div(a, b):
    if b in [0, None] or pd.isna(b):
        return np.nan
    return a / b


def diagnose_revenue_anomaly(
    df: pd.DataFrame,
    focus_date,
    baseline_days: int = 7,
) -> dict:
    """
    Diagnose revenue anomaly using exact symmetric contribution decomposition.

    revenue = sessions × conversion_rate × aov

    Output:
    - delta_pct: percentage changes of each component
    - component_contributions: additive contributions to revenue change
    - primary_driver_metric: sessions / conversion_rate / aov
    - diagnosis_type: traffic / conversion / value_per_order
    """

    out = df.copy()
    out["event_day"] = pd.to_datetime(out["event_day"])
    focus_date = pd.to_datetime(focus_date)

    baseline_start = focus_date - pd.Timedelta(days=baseline_days)

    focus_df = out[out["event_day"] == focus_date].copy()
    baseline_df = out[
        (out["event_day"] >= baseline_start) &
        (out["event_day"] < focus_date)
    ].copy()

    if focus_df.empty or baseline_df.empty:
        return {}

    # ---------- focus day ----------
    focus_sessions = float(focus_df["sessions"].sum())
    focus_transactions = float(focus_df["transactions"].sum())
    focus_revenue = float(focus_df["revenue"].sum())

    focus_conversion_rate = safe_div(focus_transactions, focus_sessions)
    focus_aov = safe_div(focus_revenue, focus_transactions)

    # ---------- baseline ----------
    baseline_daily = (
        baseline_df.groupby("event_day", as_index=False)[
            ["sessions", "transactions", "revenue"]
        ].sum()
    )

    baseline_sessions = float(baseline_daily["sessions"].mean())
    baseline_transactions = float(baseline_daily["transactions"].mean())
    baseline_revenue = float(baseline_daily["revenue"].mean())

    baseline_conversion_rate = safe_div(
        float(baseline_daily["transactions"].sum()),
        float(baseline_daily["sessions"].sum())
    )
    baseline_aov = safe_div(
        float(baseline_daily["revenue"].sum()),
        float(baseline_daily["transactions"].sum())
    )

    def pct_change(focus, baseline):
        if baseline == 0 or pd.isna(baseline):
            return None
        return (focus - baseline) / baseline

    delta_pct = {
        "revenue": pct_change(focus_revenue, baseline_revenue),
        "sessions": pct_change(focus_sessions, baseline_sessions),
        "conversion_rate": pct_change(focus_conversion_rate, baseline_conversion_rate),
        "aov": pct_change(focus_aov, baseline_aov),
    }

    # ---------- exact additive contribution decomposition ----------
    baseline_components = {
        "sessions": baseline_sessions,
        "conversion_rate": baseline_conversion_rate,
        "aov": baseline_aov,
    }

    focus_components = {
        "sessions": focus_sessions,
        "conversion_rate": focus_conversion_rate,
        "aov": focus_aov,
    }

    def revenue_from_components(comp: dict) -> float:
        s = comp["sessions"]
        c = comp["conversion_rate"]
        a = comp["aov"]

        if pd.isna(s) or pd.isna(c) or pd.isna(a):
            return np.nan

        return float(s * c * a)

    factors = ["sessions", "conversion_rate", "aov"]

    contributions = {f: 0.0 for f in factors}
    perms = list(itertools.permutations(factors))

    for perm in perms:
        current = baseline_components.copy()
        prev_rev = revenue_from_components(current)

        for f in perm:
            current[f] = focus_components[f]
            new_rev = revenue_from_components(current)

            if pd.isna(prev_rev) or pd.isna(new_rev):
                marginal = 0.0
            else:
                marginal = new_rev - prev_rev

            contributions[f] += marginal
            prev_rev = new_rev

    # average over all permutations (Shapley-style attribution)
    for f in factors:
        contributions[f] /= len(perms)

    # choose main driver by absolute contribution to revenue change
    abs_contrib = {k: abs(v) for k, v in contributions.items()}
    primary_driver_metric = max(abs_contrib, key=abs_contrib.get)

    total_abs_contrib = sum(abs_contrib.values())

    if total_abs_contrib == 0 or pd.isna(total_abs_contrib):
        contribution_pct = {k: 0.0 for k in abs_contrib}
    else:
        contribution_pct = {
            k: v / total_abs_contrib
            for k, v in abs_contrib.items()
        }

    diagnosis_type_map = {
        "sessions": "traffic",
        "conversion_rate": "conversion",
        "aov": "value_per_order",
    }
    diagnosis_type = diagnosis_type_map[primary_driver_metric]

    return {
        "focus": {
            "revenue": focus_revenue,
            "sessions": focus_sessions,
            "transactions": focus_transactions,
            "conversion_rate": focus_conversion_rate,
            "aov": focus_aov,
        },
        "baseline": {
            "revenue": baseline_revenue,
            "sessions": baseline_sessions,
            "transactions": baseline_transactions,
            "conversion_rate": baseline_conversion_rate,
            "aov": baseline_aov,
        },
        "delta_pct": delta_pct,
        "component_contributions": contributions,
        "component_abs_contributions": abs_contrib,
        "component_contribution_pct": contribution_pct,
        "diagnosis_type": diagnosis_type,
        "primary_driver_metric": primary_driver_metric,
    }