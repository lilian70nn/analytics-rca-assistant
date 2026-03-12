import plotly.express as px
import pandas as pd


def plot_decomposition_chart(ui, anomaly_index=0):
    charts = ui.get("decomposition_chart", [])

    if not charts:
        return None

    data = charts[anomaly_index]["items"]

    df = pd.DataFrame(data)

    fig = px.bar(
        df,
        x="component",
        y="value",
        title="Metric Decomposition"
    )

    fig.update_layout(
        xaxis_title="Component",
        yaxis_title="Contribution"
    )

    return fig


def build_dimension_table(ui, anomaly_index=0):
    tables = ui.get("dimension_tables", [])

    if not tables:
        return None

    rows = tables[anomaly_index]["rows"]

    output = []

    for dim in rows:
        dimension = dim["dimension"]

        for seg in dim["segments"]:
            output.append({
                "dimension": dimension,
                "segment": seg.get("segment"),
                "focus_value": seg.get("focus_value"),
                "baseline_value": seg.get("baseline_value"),
                "change": seg.get("change"),
                "segment_pct": seg.get("segment_pct_within_dimension"),
            })

    return pd.DataFrame(output)


def build_driver_table(ui, anomaly_index=0):
    tables = ui.get("driver_tables", [])

    if not tables:
        return None

    rows = tables[anomaly_index]["rows"]

    return pd.DataFrame(rows)