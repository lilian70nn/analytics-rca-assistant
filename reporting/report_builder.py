from utils.utils import deep_convert

def build_investigation_report(result):
    report = {
        "metric": result.get("metric"),
        "time_range": result.get("time_range"),
        "anomalies": []
    }

    investigations = result.get("investigations", [])

    for inv in investigations:

        diagnosis = inv.get("diagnosis", {}) or {}

        anomaly_item = {
            "date": inv.get("anomaly_day"),
            "direction": inv.get("direction"),
            "metric_value": inv.get("metric_value"),
            "z_score": inv.get("z_score"),
            "driver_metric": diagnosis.get("primary_driver_metric"),
            "diagnosis": {
                "diagnosis_type": diagnosis.get("diagnosis_type"),
                "primary_driver_metric": diagnosis.get("primary_driver_metric"),
                "component_contribution_pct": diagnosis.get("component_contribution_pct", {})
            },
            "top_dimensions": [],
            "top_drivers": inv.get("top_drivers", [])[:5],
            "metric_branches": []
        }

        for d in inv.get("top_dimensions", [])[:3]:
            anomaly_item["top_dimensions"].append({
                "dimension": d.get("dimension"),
                "dimension_pct": d.get("dimension_pct"),
                "segments": d.get("segments", [])
            })

        for branch in inv.get("metric_branches", [])[:2]:
            branch_item = {
                "metric": branch.get("metric"),
                "metric_contribution_pct": branch.get("metric_contribution_pct"),
                "top_dimensions": [],
                "top_drivers": branch.get("top_drivers", [])[:5]
            }

            for d in branch.get("top_dimensions", [])[:3]:
                branch_item["top_dimensions"].append({
                    "dimension": d.get("dimension"),
                    "dimension_pct": d.get("dimension_pct"),
                    "segments": d.get("segments", [])
                })
            anomaly_item["metric_branches"].append(branch_item)

        report["anomalies"].append(anomaly_item)

    return deep_convert(report)



def build_trend_report(result):
    trend = result.get("trend", []) or []

    report = {
        "metric": result.get("metric"),
        "time_range": result.get("time_range"),
        "summary": {},
        "series": trend
    }

    if not trend:
        return report

    values = [x.get("metric_value") for x in trend if x.get("metric_value") is not None]

    if not values:
        return report

    start_point = trend[0]
    end_point = trend[-1]

    report["summary"] = {
        "start_date": start_point.get("event_day"),
        "start_value": start_point.get("metric_value"),
        "end_date": end_point.get("event_day"),
        "end_value": end_point.get("metric_value"),
        "min_value": min(values),
        "max_value": max(values),
        "num_points": len(trend)
    }

    return report


def build_breakdown_report(result, top_k=10):
    breakdown = result.get("breakdown", []) or []

    report = {
        "metric": result.get("metric"),
        "dimension": result.get("dimension"),
        "time_range": result.get("time_range"),
        "rows": breakdown[:top_k]
    }

    return report