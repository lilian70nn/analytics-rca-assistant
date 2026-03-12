import pandas as pd
import itertools

DIMENSIONS = [
    "country",
    "region",
    "city",
    "device",
    "operating_system",
    "browser",
    "source",
    "medium",
    "campaign",
]

def dimension_breakdown(
    df: pd.DataFrame,
    focus_date,
    dimension: str = "country",
    metric: str = "revenue",
    baseline_days: int = 7,
) -> pd.DataFrame:

    out = df.copy()

    out["event_day"] = pd.to_datetime(out["event_day"])
    focus_date = pd.to_datetime(focus_date)

    baseline_start = focus_date - pd.Timedelta(days=baseline_days)

    focus_df = out[out["event_day"] == focus_date].copy()
    baseline_df = out[
        (out["event_day"] >= baseline_start) & (out["event_day"] < focus_date)
    ].copy()

    if focus_df.empty or baseline_df.empty:
        return pd.DataFrame(
            columns=[dimension, "focus_value", "baseline_value", "change", "abs_change"]
        )

    additive_metrics = [
        "revenue",
        "transactions",
        "sessions",
        "pageviews",
        "bounces",
        "time_on_site",
    ]

    if metric in additive_metrics:
        focus_agg = (
            focus_df.groupby(dimension, dropna=False)[metric]
            .sum()
            .reset_index(name="focus_value")
        )

        baseline_daily = (
            baseline_df.groupby(["event_day", dimension], dropna=False)[metric]
            .sum()
            .reset_index()
        )

        baseline_agg = (
            baseline_daily.groupby(dimension, dropna=False)[metric]
            .mean()
            .reset_index(name="baseline_value")
        )

    elif metric == "conversion_rate":
        focus_agg = (
            focus_df.groupby(dimension, dropna=False)[["transactions", "sessions"]]
            .sum()
            .reset_index()
        )
        focus_agg["focus_value"] = (
            focus_agg["transactions"] / focus_agg["sessions"].replace(0, pd.NA)
        )
        focus_agg = focus_agg[[dimension, "focus_value"]]

        baseline_daily = (
            baseline_df.groupby(["event_day", dimension], dropna=False)[["transactions", "sessions"]]
            .sum()
            .reset_index()
        )
        baseline_daily["daily_rate"] = (
            baseline_daily["transactions"] / baseline_daily["sessions"].replace(0, pd.NA)
        )

        baseline_agg = (
            baseline_daily.groupby(dimension, dropna=False)["daily_rate"]
            .mean()
            .reset_index(name="baseline_value")
        )

    elif metric == "bounce_rate":
        focus_agg = (
            focus_df.groupby(dimension, dropna=False)[["bounces", "sessions"]]
            .sum()
            .reset_index()
        )
        focus_agg["focus_value"] = (
            focus_agg["bounces"] / focus_agg["sessions"].replace(0, pd.NA)
        )
        focus_agg = focus_agg[[dimension, "focus_value"]]

        baseline_daily = (
            baseline_df.groupby(["event_day", dimension], dropna=False)[["bounces", "sessions"]]
            .sum()
            .reset_index()
        )
        baseline_daily["daily_rate"] = (
            baseline_daily["bounces"] / baseline_daily["sessions"].replace(0, pd.NA)
        )

        baseline_agg = (
            baseline_daily.groupby(dimension, dropna=False)["daily_rate"]
            .mean()
            .reset_index(name="baseline_value")
        )

    elif metric == "aov":

        focus_agg = (
            focus_df.groupby(dimension, dropna=False)[["revenue", "transactions"]]
            .sum()
            .reset_index()
        )
        focus_agg["focus_value"] = (
            focus_agg["revenue"] / focus_agg["transactions"].replace(0, pd.NA)
        )
        focus_agg = focus_agg[[dimension, "focus_value"]]

        baseline_daily = (
            baseline_df.groupby(["event_day", dimension], dropna=False)[["revenue", "transactions"]]
            .sum()
            .reset_index()
        )
        baseline_daily["daily_rate"] = (
            baseline_daily["revenue"] / baseline_daily["transactions"].replace(0, pd.NA)
        )

        baseline_agg = (
            baseline_daily.groupby(dimension, dropna=False)["daily_rate"]
            .mean()
            .reset_index(name="baseline_value")
        )

    else:
        raise ValueError(f"Unsupported metric: {metric}")

    result = focus_agg.merge(
        baseline_agg,
        on=dimension,
        how="outer"
    )

    result["focus_value"] = result["focus_value"].fillna(0)
    result["baseline_value"] = result["baseline_value"].fillna(0)

    result["change"] = result["focus_value"] - result["baseline_value"]
    result["abs_change"] = result["change"].abs()

    result = result.sort_values("abs_change", ascending=False).reset_index(drop=True)

    return result

def find_top_dimensions(df, focus_date, metric, k=3):

    scores = []

    for d in DIMENSIONS:

        breakdown = dimension_breakdown(
            df,
            focus_date=focus_date,
            dimension=d,
            metric=metric
        )

        if breakdown.empty:
            continue

        score = breakdown["abs_change"].head(5).sum()

        scores.append((d, score))

    scores.sort(key=lambda x: x[1], reverse=True)

    return [d for d,_ in scores[:k]]


def dimension_breakdown_multi(
    df,
    focus_date,
    dimensions,
    metric="revenue",
    baseline_days=7
):
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
        return pd.DataFrame()

    additive_metrics = [
        "revenue",
        "transactions",
        "sessions",
        "pageviews",
        "bounces",
        "time_on_site",
    ]

    if metric in additive_metrics:
        focus_agg = (
            focus_df
            .groupby(list(dimensions), dropna=False)[metric]
            .sum()
            .reset_index(name="focus_value")
        )

        baseline_daily = (
            baseline_df
            .groupby(["event_day"] + list(dimensions), dropna=False)[metric]
            .sum()
            .reset_index()
        )

        baseline_agg = (
            baseline_daily
            .groupby(list(dimensions), dropna=False)[metric]
            .mean()
            .reset_index(name="baseline_value")
        )

    elif metric == "conversion_rate":
        focus_agg = (
            focus_df
            .groupby(list(dimensions), dropna=False)[["transactions", "sessions"]]
            .sum()
            .reset_index()
        )

        focus_agg["focus_value"] = (
            focus_agg["transactions"] /
            focus_agg["sessions"].replace(0, pd.NA)
        )
        focus_agg = focus_agg.rename(columns={
            "sessions": "focus_sessions",
            "transactions": "focus_transactions"
        })

        baseline_daily = (
            baseline_df
            .groupby(["event_day"] + list(dimensions), dropna=False)[["transactions", "sessions"]]
            .sum()
            .reset_index()
        )

        baseline_daily["daily_rate"] = (
            baseline_daily["transactions"] /
            baseline_daily["sessions"].replace(0, pd.NA)
        )

        baseline_agg = (
            baseline_daily
            .groupby(list(dimensions), dropna=False)
            .agg(
                baseline_value=("daily_rate", "mean"),
                baseline_sessions=("sessions", "mean"),
                baseline_transactions=("transactions", "mean"),
            )
            .reset_index()
        )

        focus_agg = focus_agg[
            list(dimensions) + ["focus_value", "focus_sessions", "focus_transactions"]
        ]

    elif metric == "bounce_rate":
        focus_agg = (
            focus_df
            .groupby(list(dimensions), dropna=False)[["bounces", "sessions"]]
            .sum()
            .reset_index()
        )

        focus_agg["focus_value"] = (
            focus_agg["bounces"] /
            focus_agg["sessions"].replace(0, pd.NA)
        )
        focus_agg = focus_agg.rename(columns={
            "sessions": "focus_sessions",
            "bounces": "focus_bounces"
        })

        baseline_daily = (
            baseline_df
            .groupby(["event_day"] + list(dimensions), dropna=False)[["bounces", "sessions"]]
            .sum()
            .reset_index()
        )

        baseline_daily["daily_rate"] = (
            baseline_daily["bounces"] /
            baseline_daily["sessions"].replace(0, pd.NA)
        )

        baseline_agg = (
            baseline_daily
            .groupby(list(dimensions), dropna=False)
            .agg(
                baseline_value=("daily_rate", "mean"),
                baseline_sessions=("sessions", "mean"),
                baseline_bounces=("bounces", "mean"),
            )
            .reset_index()
        )

        focus_agg = focus_agg[
            list(dimensions) + ["focus_value", "focus_sessions", "focus_bounces"]
        ]

    elif metric == "aov":
        focus_agg = (
            focus_df
            .groupby(list(dimensions), dropna=False)[["revenue", "transactions"]]
            .sum()
            .reset_index()
        )

        focus_agg["focus_value"] = (
            focus_agg["revenue"] /
            focus_agg["transactions"].replace(0, pd.NA)
        )
        focus_agg = focus_agg.rename(columns={
            "transactions": "focus_transactions",
            "revenue": "focus_revenue"
        })

        baseline_daily = (
            baseline_df
            .groupby(["event_day"] + list(dimensions), dropna=False)[["revenue", "transactions"]]
            .sum()
            .reset_index()
        )

        baseline_daily["daily_rate"] = (
            baseline_daily["revenue"] /
            baseline_daily["transactions"].replace(0, pd.NA)
        )

        baseline_agg = (
            baseline_daily
            .groupby(list(dimensions), dropna=False)
            .agg(
                baseline_value=("daily_rate", "mean"),
                baseline_transactions=("transactions", "mean"),
                baseline_revenue=("revenue", "mean"),
            )
            .reset_index()
        )

        focus_agg = focus_agg[
            list(dimensions) + ["focus_value", "focus_transactions", "focus_revenue"]
        ]

    else:
        raise ValueError(f"Unsupported metric: {metric}")

    result = focus_agg.merge(
        baseline_agg,
        on=list(dimensions),
        how="outer"
    )

    for col in result.columns:
        if col not in list(dimensions):
            result[col] = result[col].fillna(0)

    result["change"] = result["focus_value"] - result["baseline_value"]
    result["abs_change"] = result["change"].abs()
    result["dimension"] = " × ".join(dimensions)

    result = result.sort_values(
        "abs_change",
        ascending=False
    ).reset_index(drop=True)

    return result

def compute_driver_contributions(drivers: pd.DataFrame):

    if drivers.empty:
        return drivers

    out = drivers.copy()

    total_change = out["change"].sum()

    if total_change == 0:
        out["contribution"] = 0
        return out

    if total_change < 0:
        relevant = out[out["change"] < 0].copy()
    else:
        relevant = out[out["change"] > 0].copy()

    total_change = relevant["change"].sum() 

    relevant["contribution"] = relevant["change"] / total_change
    relevant["abs_contribution"] = relevant["contribution"].abs()

    relevant = relevant.sort_values(
        "abs_contribution",
        ascending=False
    )

    return relevant.reset_index(drop=True)


def parse_driver_signature(row) -> dict:
    """
    Convert a driver row into a dict signature.

    Example:
    dimension = "device × browser"
    segment   = "desktop | Chrome"

    ->
    {
        "device": "desktop",
        "browser": "Chrome"
    }
    """
    dims = [d.strip() for d in str(row["dimension"]).split("×")]
    vals = [v.strip() for v in str(row["segment"]).split("|")]

    if len(dims) != len(vals):
        return {}

    return dict(zip(dims, vals))


def is_driver_overlapping(candidate_sig: dict, selected_sig: dict) -> bool:
    """
    Two drivers overlap if one is a subset of the other on shared dimensions.

    Example:
    {"device": "desktop"} overlaps with
    {"device": "desktop", "browser": "Chrome"}

    because the smaller one is fully contained in the larger one.
    """
    if not candidate_sig or not selected_sig:
        return False

    shared_dims = set(candidate_sig.keys()) & set(selected_sig.keys())

    if not shared_dims:
        return False

    # shared dimensions must have identical values
    same_on_shared = all(candidate_sig[d] == selected_sig[d] for d in shared_dims)
    if not same_on_shared:
        return False

    # if one signature is subset/superset of the other, treat as overlap
    candidate_items = set(candidate_sig.items())
    selected_items = set(selected_sig.items())

    return (
        candidate_items.issubset(selected_items)
        or selected_items.issubset(candidate_items)
    )



def deduplicate_drivers(drivers: pd.DataFrame, top_k: int = 10) -> pd.DataFrame:
    """
    Greedy driver selection:
    - assume drivers are already sorted by importance
    - keep the first informative driver
    - skip later drivers if they overlap strongly with an already selected one
    """
    if drivers.empty:
        return drivers

    selected_rows = []
    selected_sigs = []

    for _, row in drivers.iterrows():
        candidate_sig = parse_driver_signature(row)

        overlap = any(
            is_driver_overlapping(candidate_sig, sig)
            for sig in selected_sigs
        )

        if overlap:
            continue

        selected_rows.append(row)
        selected_sigs.append(candidate_sig)

        if len(selected_rows) >= top_k:
            break

    if not selected_rows:
        return pd.DataFrame(columns=drivers.columns)

    return pd.DataFrame(selected_rows).reset_index(drop=True)


def root_cause_ranking(
    df,
    focus_date,
    metric="revenue",
    dimensions=None,
    baseline_days=7,
    top_k=10,
):
    """
    Scan multiple dimensions to find segments driving the change.
    """

    if dimensions is None:
        dimensions = DIMENSIONS

    top_dims = find_top_dimensions(
        df,
        focus_date,
        metric,
        k=3
    )

    candidates = []

    for d in dimensions:
        candidates.append((d,))

    # pair only among top dimensions
    for combo in itertools.combinations(top_dims, 2):
        candidates.append(combo)

    all_drivers = []

    for dims in candidates:

        breakdown = dimension_breakdown_multi(
            df,
            focus_date=focus_date,
            dimensions=dims,
            metric=metric,
            baseline_days=baseline_days,
        )

        if breakdown.empty:
            continue

        breakdown = breakdown.copy()
        breakdown["segment"] = breakdown[list(dims)].astype(str).agg(" | ".join, axis=1)
        breakdown["dimension"] = " × ".join(dims)

        keep_cols = [
            "dimension",
            "segment",
            "focus_value",
            "baseline_value",
            "change",
            "abs_change",
        ]

        extra_cols = [
            c for c in [
                "focus_sessions", "baseline_sessions",
                "focus_transactions", "baseline_transactions",
                "focus_revenue", "baseline_revenue",
                "focus_bounces", "baseline_bounces",
            ]
            if c in breakdown.columns
        ]

        all_drivers.append(
            breakdown[keep_cols + extra_cols]
        )

    if not all_drivers:
        return pd.DataFrame()

    drivers = pd.concat(all_drivers)

    ratio_metrics = {"conversion_rate", "aov", "bounce_rate"}

    if metric in ratio_metrics:

        drivers = drivers.copy()

        if metric in {"conversion_rate", "bounce_rate"}:
            drivers["impact"] = drivers["abs_change"] * drivers["baseline_sessions"]

        elif metric == "aov":
            drivers["impact"] = drivers["abs_change"] * drivers["baseline_transactions"]

        total_impact = drivers["impact"].sum()

        if total_impact == 0 or pd.isna(total_impact):
            drivers["contribution"] = 0.0
            drivers["abs_contribution"] = 0.0
        else:
            drivers["contribution"] = drivers["impact"] / total_impact
            drivers["abs_contribution"] = drivers["contribution"].abs()

        drivers = drivers.sort_values(
            ["abs_contribution", "abs_change"],
            ascending=False
        ).reset_index(drop=True)

    else:

        drivers = compute_driver_contributions(drivers)

        drivers = drivers.sort_values(
            ["abs_contribution", "abs_change"],
            ascending=False
        ).reset_index(drop=True)

    drivers = deduplicate_drivers(drivers, top_k=top_k)

    return drivers


def build_top_dimensions(
    df: pd.DataFrame,
    focus_date,
    metric: str,
    baseline_days: int = 7,
    top_k_dimensions: int = 2,
    top_k_segments: int = 3,
):
    """
    Build dimension-level summary for the chosen driver metric.

    Output structure:
    [
      {
        "dimension": "country",
        "dimension_score": ...,
        "dimension_pct": ...,
        "segments": [
          {
            "segment": "United States",
            "focus_value": ...,
            "baseline_value": ...,
            "change": ...,
            "abs_change": ...,
            "segment_pct_within_dimension": ...
          },
          ...
        ]
      },
      ...
    ]
    """

    dimension_results = []

    for d in DIMENSIONS:
        breakdown = dimension_breakdown(
            df,
            focus_date=focus_date,
            dimension=d,
            metric=metric,
            baseline_days=baseline_days,
        )

        if breakdown.empty:
            continue

        breakdown = breakdown.copy()

        dimension_score = breakdown["abs_change"].sum()

        if dimension_score <= 0 or pd.isna(dimension_score):
            continue

        top_segments_df = breakdown.head(top_k_segments).copy()
        other_df = breakdown.iloc[top_k_segments:].copy()

        segments = []

        for _, row in top_segments_df.iterrows():
            seg_name = row[d]
            segments.append({
                "segment": None if pd.isna(seg_name) else str(seg_name),
                "focus_value": row["focus_value"],
                "baseline_value": row["baseline_value"],
                "change": row["change"],
                "abs_change": row["abs_change"],
                "segment_pct_within_dimension": row["abs_change"] / dimension_score
            })


        if not other_df.empty:
            other_focus = other_df["focus_value"].sum()
            other_baseline = other_df["baseline_value"].sum()


            other_change = other_focus - other_baseline
            other_abs_change = other_df["abs_change"].sum()

            segments.append({
                "segment": "__OTHER__",
                "focus_value": other_focus,
                "baseline_value": other_baseline,
                "change": other_change,
                "abs_change": other_abs_change,
                "segment_pct_within_dimension": other_abs_change / dimension_score
            })

        dimension_results.append({
            "dimension": d,
            "dimension_score": dimension_score,
            "segments": segments
        })

    if not dimension_results:
        return []

    total_dimension_score = sum(x["dimension_score"] for x in dimension_results)

    for item in dimension_results:
        if total_dimension_score == 0 or pd.isna(total_dimension_score):
            item["dimension_pct"] = 0.0
        else:
            item["dimension_pct"] = item["dimension_score"] / total_dimension_score


    dimension_results = sorted(
        dimension_results,
        key=lambda x: x["dimension_score"],
        reverse=True
    )[:top_k_dimensions]

    return dimension_results