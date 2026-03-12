from reporting.report_builder import build_investigation_report

def format_pct(x):
    if x is None:
        return "N/A"
    return f"{x * 100:.1f}%"


def explain_investigation_template(report):
    anomalies = report.get("anomalies", [])
    metric = report.get("metric", "metric")

    if not anomalies:
        return "No anomalies were detected."

    parts = []

    for a in anomalies:
        date = a.get("date")
        direction = a.get("direction")
        metric_value = a.get("metric_value")
        z_score = a.get("z_score")
        driver_metric = a.get("driver_metric")

        diagnosis = a.get("diagnosis") or {}
        diagnosis_type = diagnosis.get("diagnosis_type")
        contribution_pct = diagnosis.get("component_contribution_pct") or {}

        top_dimensions = a.get("top_dimensions", [])[:3]
        top_drivers = a.get("top_drivers", [])[:3]

        line = []

        # ---------- anomaly summary ----------
        z_text = f"{z_score:.2f}" if z_score is not None else "N/A"
        line.append(
            f"On {date}, a {direction} anomaly was detected in {metric} "
            f"(value={metric_value}, z_score={z_text})."
        )

        # ---------- metric diagnosis ----------
        if driver_metric:
            line.append(
                f"The primary driver metric was {driver_metric}"
                + (f" ({diagnosis_type})." if diagnosis_type else ".")
            )

        if contribution_pct:
            ordered_components = ["sessions", "conversion_rate", "aov"]
            contrib_items = []

            for k in ordered_components:
                if k in contribution_pct:
                    contrib_items.append(f"{k}={format_pct(contribution_pct[k])}")

            for k, v in contribution_pct.items():
                if k not in ordered_components:
                    contrib_items.append(f"{k}={format_pct(v)}")

            line.append(
                "Metric contribution split: "
                + ", ".join(contrib_items)
                + "."
            )

        # ---------- top dimensions ----------
        if top_dimensions:
            dim_texts = []

            for d in top_dimensions:
                dim_name = d.get("dimension")
                dim_pct = d.get("dimension_pct")

                # 每个 dimension 只展示前 3 个 segment，避免太长
                visible_segments = []
                for s in d.get("segments", [])[:3]:
                    seg_name = s.get("segment")
                    seg_pct = s.get("segment_pct_within_dimension")

                    if seg_name == "__OTHER__":
                        continue

                    visible_segments.append(
                        f"{seg_name} ({format_pct(seg_pct)})"
                    )

                dim_text = f"{dim_name} ({format_pct(dim_pct)})"
                if visible_segments:
                    dim_text += ": " + ", ".join(visible_segments)

                dim_texts.append(dim_text)

            if dim_texts:
                line.append(
                    "Top dimensions contributing to the change were: "
                    + "; ".join(dim_texts)
                    + "."
                )

        # ---------- top drivers ----------
        if top_drivers:
            driver_text = "; ".join(
                f"{d.get('dimension')} → {d.get('segment')}"
                + (
                    f" ({format_pct(d.get('contribution'))})"
                    if d.get("contribution") is not None else ""
                )
                for d in top_drivers
            )
            line.append(f"Additional top driver patterns: {driver_text}.")

        parts.append(" ".join(line))

    return "\n\n".join(parts)


def explain_trend_template(result):
    trend = result.get("trend", [])
    metric = result.get("metric", "metric")
    time_range = result.get("time_range", {})

    if not trend:
        return "No trend data is available."

    values = [x["metric_value"] for x in trend if x.get("metric_value") is not None]

    start_point = trend[0]
    end_point = trend[-1]

    return (
        f"The {metric} trend from {time_range.get('start_date')} to {time_range.get('end_date')} "
        f"contains {len(trend)} data points. "
        f"It started at {start_point.get('metric_value')} on {start_point.get('event_day')} "
        f"and ended at {end_point.get('metric_value')} on {end_point.get('event_day')}. "
        f"The minimum value was {min(values)} and the maximum value was {max(values)}."
    )


def explain_breakdown_template(result):
    metric = result.get("metric", "metric")
    dimension = result.get("dimension", "dimension")
    breakdown = result.get("breakdown", [])[:5]
    time_range = result.get("time_range", {})

    if not breakdown:
        return "No breakdown data is available."

    lines = [
        f"The top {metric} segments by {dimension} from "
        f"{time_range.get('start_date')} to {time_range.get('end_date')} are:"
    ]

    for row in breakdown:
        lines.append(f"- {row.get(dimension)}: {row.get('metric_value')}")

    return "\n".join(lines)


def explain_analysis(question, analysis_type, result):
    if isinstance(result, dict) and "error" in result:
        return result["error"]

    if analysis_type == "investigate":
        report = build_investigation_report(result)
        return explain_investigation_template(report)
    elif analysis_type == "trend":
        return explain_trend_template(result)
    elif analysis_type == "breakdown":
        return explain_breakdown_template(result)
    else:
        return "Unsupported analysis type."

# SYSTEM_PROMPT = """
# You are a data analyst explaining analytics results.

# Rules:
# - Use only the information in the provided summary.
# - Do not invent causes, recommendations, implications, or business context.
# - Do not infer anything that is not explicitly stated in the summary.
# - If a field is missing, do not guess.
# - Be concise and factual.

# If analysis_type is "investigate":
# - explain which anomaly days were detected
# - state the driver_metric if provided
# - state the diagnosis_type if provided
# - describe component_contribution_pct if provided
# - describe the listed top_drivers only
# - do not add deeper reasons beyond the listed drivers

# If analysis_type is "trend":
# - summarize the overall trend using only the start_point, end_point, min_value, and max_value

# If analysis_type is "breakdown":
# - summarize the top_segments only
# """


# def build_investigation_summary(result):
#     summary = {
#         "analysis_type": "investigate",
#         "metric": result["metric"],
#         "time_range": result["time_range"],
#         "anomalies": []
#     }

#     for investigation in result.get("investigations", []):
#         top_drivers = investigation.get("top_drivers", [])[:3]
#         diagnosis = investigation.get("diagnosis", {}) or {}

#         summary["anomalies"].append({
#             "date": investigation.get("anomaly_day"),
#             "direction": investigation.get("direction"),
#             "metric_value": investigation.get("metric_value"),
#             "z_score": investigation.get("z_score"),
#             "driver_metric": investigation.get("driver_metric"),
#             "diagnosis_type": diagnosis.get("diagnosis_type"),
#             "component_contributions": diagnosis.get("component_contributions"),
#             "component_contribution_pct": diagnosis.get("component_contribution_pct"),
#             "top_drivers": [
#                 {
#                     "dimension": d.get("dimension"),
#                     "segment": d.get("segment")
#                 }
#                 for d in top_drivers
#             ]
#         })

#     return summary


# def build_trend_summary(result):
#     trend = result.get("trend", [])

#     if not trend:
#         return {
#             "analysis_type": "trend",
#             "metric": result["metric"],
#             "time_range": result["time_range"],
#             "num_points": 0,
#             "start_point": None,
#             "end_point": None,
#             "min_value": None,
#             "max_value": None
#         }

#     values = [
#         x["metric_value"]
#         for x in trend
#         if x.get("metric_value") is not None
#     ]

#     return {
#         "analysis_type": "trend",
#         "metric": result["metric"],
#         "time_range": result["time_range"],
#         "num_points": len(trend),
#         "start_point": trend[0],
#         "end_point": trend[-1],
#         "min_value": min(values) if values else None,
#         "max_value": max(values) if values else None
#     }


# def build_breakdown_summary(result):
#     breakdown = result.get("breakdown", [])

#     return {
#         "analysis_type": "breakdown",
#         "metric": result["metric"],
#         "dimension": result["dimension"],
#         "time_range": result["time_range"],
#         "top_segments": breakdown[:5]
#     }


# def build_summary(analysis_type, result):
#     if analysis_type == "investigate":
#         return build_investigation_summary(result)
#     elif analysis_type == "trend":
#         return build_trend_summary(result)
#     elif analysis_type == "breakdown":
#         return build_breakdown_summary(result)
#     else:
#         raise ValueError(f"Unsupported analysis type: {analysis_type}")


# def explain_analysis(question, analysis_type, result):
#     if isinstance(result, dict) and "error" in result:
#         return result["error"]

#     summary = build_summary(analysis_type, result)

#     prompt = f"""
# User question:
# {question}

# Analysis summary:
# {json.dumps(summary, default=str, indent=2)}

# Explain the result using only the summary.
# Do not infer hidden causes.
# If analysis_type is investigate, first explain the metric-level diagnosis, then explain the top dimension drivers.
# """

#     response = ollama.chat(
#         model="qwen2.5-coder:7b",
#         messages=[
#             {"role": "system", "content": SYSTEM_PROMPT},
#             {"role": "user", "content": prompt}
#         ]
#     )

#     explanation = response["message"]["content"]

#     return explanation