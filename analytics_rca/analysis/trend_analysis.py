from data.loader import load_fact_sessions
from utils.serialization import dataframe_to_records
import pandas as pd

def get_metric_trend(df, metric="revenue"):

    additive_metrics = [
        "revenue",
        "transactions",
        "sessions",
        "pageviews",
        "bounces",
        "time_on_site",
    ]

    if metric in additive_metrics:

        trend = (
            df.groupby("event_day", as_index=False)[metric]
            .sum()
            .rename(columns={metric: "metric_value"})
        )

    elif metric == "conversion_rate":

        tmp = (
            df.groupby("event_day")[["transactions", "sessions"]]
            .sum()
            .reset_index()
        )

        tmp["metric_value"] = tmp["transactions"] / tmp["sessions"].replace(0, pd.NA)

        trend = tmp[["event_day", "metric_value"]]

    elif metric == "bounce_rate":

        tmp = (
            df.groupby("event_day")[["bounces", "sessions"]]
            .sum()
            .reset_index()
        )

        tmp["metric_value"] = tmp["bounces"] / tmp["sessions"].replace(0, pd.NA)

        trend = tmp[["event_day", "metric_value"]]

    else:
        raise ValueError(f"Unsupported metric: {metric}")

    trend["metric"] = metric

    return trend


def run_trend_analysis(
    client,
    start_date,
    end_date,
    metric
):

    df = load_fact_sessions(
        client,
        start_date=start_date,
        end_date=end_date
    )

    trend = get_metric_trend(
        df,
        metric=metric
    )

    return {
        "metric": metric,
        "time_range": {
            "start_date": start_date,
            "end_date": end_date
        },
        "trend": dataframe_to_records(trend)
    }
