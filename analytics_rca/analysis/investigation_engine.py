from data.loader import load_fact_sessions
from analytics_rca.engine.anomaly_detection import get_daily_metric, detect_anomalies
from analytics_rca.engine.metric_decomposition import diagnose_revenue_anomaly
from analytics_rca.engine.root_cause import root_cause_ranking, build_top_dimensions
from utils.serialization import dataframe_to_records


def select_metric_branches(diagnosis: dict, top_k: int = 2, min_pct: float = 0.15):
    """
    Select top metric branches from revenue decomposition.

    Rules:
    - sort by contribution pct descending
    - keep top_k
    - only keep branches with contribution >= min_pct
    """
    if not diagnosis:
        return []

    contrib = diagnosis.get("component_contribution_pct", {}) or {}
    if not contrib:
        return []

    items = [
        {"metric": k, "contribution_pct": v}
        for k, v in contrib.items()
        if v is not None
    ]

    items = sorted(items, key=lambda x: x["contribution_pct"], reverse=True)

    selected = [
        x for x in items
        if x["contribution_pct"] >= min_pct
    ][:top_k]

    return selected


# def run_investigation(
#     client,
#     start_date,
#     end_date,
#     metric="revenue",
#     window=7,
#     z_threshold=2.5,
#     direction=None,
#     top_drivers=5,
# ):
#     fact_sessions = load_fact_sessions(
#         client,
#         start_date=start_date,
#         end_date=end_date
#     )

#     daily_metric = get_daily_metric(
#         fact_sessions,
#         metric=metric
#     )

#     anomaly_df = detect_anomalies(
#         daily_metric,
#         window=window,
#         z_threshold=z_threshold
#     )

#     anomalies = anomaly_df[anomaly_df["is_anomaly"]].copy()

#     if direction in {"drop", "spike"}:
#         anomalies = anomalies[anomalies["direction"] == direction].copy()

#     anomalies = (
#         anomalies
#         .sort_values("abs_z", ascending=False)
#         .reset_index(drop=True)
#     )

#     investigations = []

#     for _, row in anomalies.iterrows():

#         anomaly_day = row["event_day"]

#         diagnosis = None
#         driver_metric = metric

#         if metric == "revenue":
#             diagnosis = diagnose_revenue_anomaly(
#                 fact_sessions,
#                 focus_date=anomaly_day
#             )
#             driver_metric = diagnosis.get("primary_driver_metric", "revenue")

#         drivers = root_cause_ranking(
#             fact_sessions,
#             focus_date=anomaly_day,
#             metric=driver_metric
#         )

#         top_dimensions = build_top_dimensions(
#             fact_sessions,
#             focus_date=anomaly_day,
#             metric=driver_metric,
#             baseline_days=7,
#             top_k_dimensions=3,
#             top_k_segments=5,
#         )


#         investigation = {
#             "anomaly_day": str(anomaly_day),
#             "direction": row["direction"],
#             "metric_value": row["metric_value"],
#             "z_score": row["z_score"],
#             "driver_metric": driver_metric,
#             "diagnosis": diagnosis,
#             "top_dimensions": top_dimensions,
#             "top_drivers": dataframe_to_records(drivers.head(top_drivers))
#         }

#         investigations.append(investigation)

#     result = {
#         "metric": metric,
#         "time_range": {
#             "start_date": start_date,
#             "end_date": end_date
#         },
#         "daily_metrics": dataframe_to_records(
#             daily_metric[["event_day", "metric_value"]]
#         ),
#         "anomalies": dataframe_to_records(
#             anomalies[["event_day", "metric_value", "z_score", "abs_z", "direction"]]
#         ),
#         "investigations": investigations
#     }

#     return result



def run_investigation(
    client,
    start_date,
    end_date,
    metric="revenue",
    window=7,
    z_threshold=2.5,
    direction=None,
    top_drivers=5,
):
    fact_sessions = load_fact_sessions(
        client,
        start_date=start_date,
        end_date=end_date
    )

    daily_metric = get_daily_metric(
        fact_sessions,
        metric=metric
    )

    anomaly_df = detect_anomalies(
        daily_metric,
        window=window,
        z_threshold=z_threshold
    )

    anomalies = anomaly_df[anomaly_df["is_anomaly"]].copy()

    if direction in {"drop", "spike"}:
        anomalies = anomalies[anomalies["direction"] == direction].copy()

    anomalies = (
        anomalies
        .sort_values("abs_z", ascending=False)
        .reset_index(drop=True)
    )

    investigations = []

    for _, row in anomalies.iterrows():

        anomaly_day = row["event_day"]

        diagnosis = None
        metric_branches = []

        if metric == "revenue":
            diagnosis = diagnose_revenue_anomaly(
                fact_sessions,
                focus_date=anomaly_day
            )

            selected_branches = select_metric_branches(
                diagnosis,
                top_k=2,
                min_pct=0.15,
            )

            for branch in selected_branches:
                branch_metric = branch["metric"]
                branch_pct = branch["contribution_pct"]

                branch_drivers = root_cause_ranking(
                    fact_sessions,
                    focus_date=anomaly_day,
                    metric=branch_metric
                )

                branch_top_dimensions = build_top_dimensions(
                    fact_sessions,
                    focus_date=anomaly_day,
                    metric=branch_metric,
                    baseline_days=7,
                    top_k_dimensions=3,
                    top_k_segments=5,
                )

                metric_branches.append({
                    "metric": branch_metric,
                    "metric_contribution_pct": branch_pct,
                    "top_dimensions": branch_top_dimensions,
                    "top_drivers": dataframe_to_records(branch_drivers.head(top_drivers))
                })

        else:
            # non-revenue metrics: keep single branch behavior
            branch_drivers = root_cause_ranking(
                fact_sessions,
                focus_date=anomaly_day,
                metric=metric
            )

            branch_top_dimensions = build_top_dimensions(
                fact_sessions,
                focus_date=anomaly_day,
                metric=metric,
                baseline_days=7,
                top_k_dimensions=3,
                top_k_segments=5,
            )

            metric_branches.append({
                "metric": metric,
                "metric_contribution_pct": 1.0,
                "top_dimensions": branch_top_dimensions,
                "top_drivers": dataframe_to_records(branch_drivers.head(top_drivers))
            })

        investigation = {
            "anomaly_day": str(anomaly_day),
            "direction": row["direction"],
            "metric_value": row["metric_value"],
            "z_score": row["z_score"],
            "diagnosis": diagnosis,
            "metric_branches": metric_branches
        }

        investigations.append(investigation)

    result = {
        "metric": metric,
        "time_range": {
            "start_date": start_date,
            "end_date": end_date
        },
        "daily_metrics": dataframe_to_records(
            daily_metric[["event_day", "metric_value"]]
        ),
        "anomalies": dataframe_to_records(
            anomalies[["event_day", "metric_value", "z_score", "abs_z", "direction"]]
        ),
        "investigations": investigations
    }

    return result