import pandas as pd
import numpy as np

def get_daily_metric(df, metric="revenue"):
    if metric in [
        "revenue",
        "transactions",
        "sessions",
        "pageviews",
        "bounces",
        "time_on_site",
    ]:
        daily = (
            df.groupby("event_day", as_index=False)[metric]
            .sum()
            .rename(columns={metric: "metric_value"})
        )

    elif metric == "conversion_rate":
        daily = (
            df.groupby("event_day", as_index=False)[["transactions", "sessions"]]
            .sum()
        )
        daily["metric_value"] = daily["transactions"] / daily["sessions"]

    elif metric == "bounce_rate":
        daily = (
            df.groupby("event_day", as_index=False)[["bounces", "sessions"]]
            .sum()
        )
        daily["metric_value"] = daily["bounces"] / daily["sessions"]

    else:
        raise ValueError("Unsupported metric")

    daily["metric"] = metric
    daily = daily[["event_day", "metric_value", "metric"]]
    return daily



def detect_anomalies(
    daily_df: pd.DataFrame,
    window: int = 7,
    z_threshold: float = 2.5,
) -> pd.DataFrame:
    df = daily_df.copy().sort_values("event_day").reset_index(drop=True)

    if df.empty:
        return df

    metric_name = df["metric"].iloc[0]
    df["detect_value"] = df["metric_value"].astype(float)

    if metric_name in [
        "revenue",
        "transactions",
        "sessions",
        "pageviews",
        "bounces",
        "time_on_site",
    ]:
        df["detect_value"] = np.log1p(df["detect_value"])

    df["rolling_median"] = (
        df["detect_value"]
        .rolling(window=window, min_periods=3)
        .median()
        .shift(1)
    )

    df["rolling_mad"] = (
        df["detect_value"]
        .rolling(window=window, min_periods=3)
        .apply(lambda x: np.median(np.abs(x - np.median(x))), raw=True)
        .shift(1)
    )

    df["rolling_mad"] = df["rolling_mad"].replace(0, np.nan)

    df["z_score"] = 0.6745 * (
        (df["detect_value"] - df["rolling_median"]) / df["rolling_mad"]
    )

    df["abs_z"] = df["z_score"].abs()
    df["is_anomaly"] = df["abs_z"] > z_threshold

    def get_direction(z):
        if pd.isna(z):
            return "normal"
        if z > 0:
            return "spike"
        if z < 0:
            return "drop"
        return "normal"

    df["direction"] = df["z_score"].apply(get_direction)

    return df