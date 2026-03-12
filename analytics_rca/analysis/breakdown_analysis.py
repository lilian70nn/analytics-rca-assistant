from data.loader import load_fact_sessions
from utils.serialization import dataframe_to_records
import pandas as pd

def metric_by_dimension(
    df,
    dimension,
    metric="revenue"
):

    additive_metrics = [
        "revenue",
        "transactions",
        "sessions",
        "pageviews",
        "bounces",
        "time_on_site",
    ]

    if metric in additive_metrics:

        result = (
            df.groupby(dimension, dropna=False)[metric]
            .sum()
            .reset_index()
            .rename(columns={metric: "metric_value"})
        )

    elif metric == "conversion_rate":

        tmp = (
            df.groupby(dimension, dropna=False)[["transactions", "sessions"]]
            .sum()
            .reset_index()
        )

        tmp["metric_value"] = tmp["transactions"] / tmp["sessions"].replace(0, pd.NA)

        result = tmp[[dimension, "metric_value"]]

    elif metric == "bounce_rate":

        tmp = (
            df.groupby(dimension, dropna=False)[["bounces", "sessions"]]
            .sum()
            .reset_index()
        )

        tmp["metric_value"] = tmp["bounces"] / tmp["sessions"].replace(0, pd.NA)

        result = tmp[[dimension, "metric_value"]]

    else:
        raise ValueError(f"Unsupported metric: {metric}")

    result["metric"] = metric

    result = result.sort_values("metric_value", ascending=False).reset_index(drop=True)

    return result


def run_breakdown_analysis(
    client,
    start_date,
    end_date,
    metric,
    dimension
):

    df = load_fact_sessions(
        client,
        start_date=start_date,
        end_date=end_date
    )

    breakdown = metric_by_dimension(
        df,
        dimension=dimension,
        metric=metric
    )

    return {
        "metric": metric,
        "dimension": dimension,
        "time_range": {
            "start_date": start_date,
            "end_date": end_date
        },
        "breakdown": dataframe_to_records(breakdown)
    }