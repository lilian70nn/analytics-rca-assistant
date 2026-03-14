from utils.utils import deep_convert

def build_investigation_ui(report):
    anomalies = report.get("anomalies", [])
    if not anomalies:
        return {
            "summary_cards": [],
            "decomposition_chart": [],
            "dimension_tables": [],
            "driver_tables": []
        }

    ui = {
        "summary_cards": [],
        "decomposition_chart": [],
        "dimension_tables": [],
        "driver_tables": []
    }

    for a in anomalies:
        diagnosis = a.get("diagnosis") or {}
        metric_branches = a.get("metric_branches", []) or []

        # 1) summary
        ui["summary_cards"].append({
            "date": a.get("date"),
            "direction": a.get("direction"),
            "metric_value": a.get("metric_value"),
            "z_score": a.get("z_score"),
            "driver_metric": a.get("driver_metric"),
            "diagnosis_type": diagnosis.get("diagnosis_type"),
        })

        # 2) decomposition
        contrib = diagnosis.get("component_contribution_pct") or {}
        ui["decomposition_chart"].append({
            "date": a.get("date"),
            "items": [
                {"component": "sessions", "value": contrib.get("sessions")},
                {"component": "conversion_rate", "value": contrib.get("conversion_rate")},
                {"component": "aov", "value": contrib.get("aov")},
            ]
        })

        # 3) dimension tables (multi-branch)
        dim_branch_rows = []

        if metric_branches:

            for branch in metric_branches[:2]:
                branch_dim_rows = []

                for d in branch.get("top_dimensions", [])[:3]:
                    branch_dim_rows.append({
                        "dimension": d.get("dimension"),
                        "dimension_pct": d.get("dimension_pct"),
                        "segments": [
                            {
                                "segment": s.get("segment"),
                                "focus_value": s.get("focus_value"),
                                "baseline_value": s.get("baseline_value"),
                                "change": s.get("change"),
                                "segment_pct_within_dimension": s.get("segment_pct_within_dimension"),
                            }
                            for s in d.get("segments", [])
                            if s.get("segment") != "__OTHER__"
                        ]
                    })

                dim_branch_rows.append({
                    "metric": branch.get("metric"),
                    "metric_contribution_pct": branch.get("metric_contribution_pct"),
                    "rows": branch_dim_rows
                })
        else:
            fallback_rows = []
            for d in a.get("top_dimensions", [])[:3]:
                fallback_rows.append({
                    "dimension": d.get("dimension"),
                    "dimension_pct": d.get("dimension_pct"),
                    "segments": [
                        {
                            "segment": s.get("segment"),
                            "focus_value": s.get("focus_value"),
                            "baseline_value": s.get("baseline_value"),
                            "change": s.get("change"),
                            "segment_pct_within_dimension": s.get("segment_pct_within_dimension"),
                        }
                        for s in d.get("segments", [])
                        if s.get("segment") != "__OTHER__"
                    ]
                })

            dim_branch_rows.append({
                "metric": a.get("driver_metric"),
                "metric_contribution_pct": None,
                "rows": fallback_rows
            })
        
        ui["dimension_tables"].append({
            "date": a.get("date"),
            "branches": dim_branch_rows
        })

        driver_branch_rows = []

        if metric_branches:
            for branch in metric_branches[:2]:
                branch_driver_rows = []

                for d in branch.get("top_drivers", [])[:5]:
                    branch_driver_rows.append({
                        "dimension": d.get("dimension"),
                        "segment": d.get("segment"),
                        "focus_value": d.get("focus_value"),
                        "baseline_value": d.get("baseline_value"),
                        "change": d.get("change"),
                        "contribution": d.get("contribution"),
                    })

                driver_branch_rows.append({
                    "metric": branch.get("metric"),
                    "metric_contribution_pct": branch.get("metric_contribution_pct"),
                    "rows": branch_driver_rows
                })
        else:
            # backward compatibility
            fallback_driver_rows = []
            for d in a.get("top_drivers", [])[:5]:
                fallback_driver_rows.append({
                    "dimension": d.get("dimension"),
                    "segment": d.get("segment"),
                    "focus_value": d.get("focus_value"),
                    "baseline_value": d.get("baseline_value"),
                    "change": d.get("change"),
                    "contribution": d.get("contribution"),
                })

            driver_branch_rows.append({
                "metric": a.get("driver_metric"),
                "metric_contribution_pct": None,
                "rows": fallback_driver_rows
            })

        ui["driver_tables"].append({
            "date": a.get("date"),
            "branches": driver_branch_rows
        })          

    return deep_convert(ui)


def build_trend_ui(report):
    summary = report.get("summary", {}) or {}
    series = report.get("series", []) or []

    ui = {
        "summary_cards": [],
        "line_chart": []
    }

    if summary:
        ui["summary_cards"] = [
            {
                "label": "Start",
                "date": summary.get("start_date"),
                "value": summary.get("start_value")
            },
            {
                "label": "End",
                "date": summary.get("end_date"),
                "value": summary.get("end_value")
            },
            {
                "label": "Min",
                "value": summary.get("min_value")
            },
            {
                "label": "Max",
                "value": summary.get("max_value")
            },
            {
                "label": "Points",
                "value": summary.get("num_points")
            }
        ]

    ui["line_chart"] = [
        {
            "date": row.get("event_day"),
            "value": row.get("metric_value")
        }
        for row in series
    ]

    return deep_convert(ui)


def build_breakdown_ui(report):
    rows = report.get("rows", []) or []
    dimension = report.get("dimension")

    ui = {
        "summary_cards": [],
        "bar_chart": [],
        "table_rows": []
    }

    if rows:
        top_row = rows[0]
        ui["summary_cards"] = [
            {
                "label": "Top Segment",
                "segment": top_row.get(dimension),
                "value": top_row.get("metric_value")
            },
            {
                "label": "Segments Shown",
                "value": len(rows)
            }
        ]

    ui["bar_chart"] = [
        {
            "segment": row.get(dimension),
            "value": row.get("metric_value")
        }
        for row in rows
    ]

    ui["table_rows"] = [
        {
            "rank": idx + 1,
            "segment": row.get(dimension),
            "value": row.get("metric_value")
        }
        for idx, row in enumerate(rows)
    ]

    return deep_convert(ui)