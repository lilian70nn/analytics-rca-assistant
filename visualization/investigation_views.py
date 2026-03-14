import pandas as pd
import plotly.express as px


def plot_decomposition_chart(ui, anomaly_index=0):
    charts = ui.get("decomposition_chart", [])

    if not charts:
        return None

    if anomaly_index >= len(charts):
        return None

    data = charts[anomaly_index].get("items", [])
    if not data:
        return None

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


def get_dimension_branches(ui, anomaly_index=0):
    tables = ui.get("dimension_tables", [])

    if not tables:
        return []

    if anomaly_index >= len(tables):
        return []

    return tables[anomaly_index].get("branches", [])


def get_driver_branches(ui, anomaly_index=0):
    tables = ui.get("driver_tables", [])

    if not tables:
        return []

    if anomaly_index >= len(tables):
        return []

    return tables[anomaly_index].get("branches", [])


def build_dimension_table(ui, anomaly_index=0, branch_index=0):
    branches = get_dimension_branches(ui, anomaly_index=anomaly_index)

    if not branches:
        return None

    if branch_index >= len(branches):
        return None

    rows = branches[branch_index].get("rows", [])
    if not rows:
        return None

    output = []

    for dim in rows:
        dimension = dim.get("dimension")

        for seg in dim.get("segments", []):
            output.append({
                "dimension": dimension,
                "segment": seg.get("segment"),
                "focus_value": seg.get("focus_value"),
                "baseline_value": seg.get("baseline_value"),
                "change": seg.get("change"),
                "segment_pct": seg.get("segment_pct_within_dimension"),
            })

    return pd.DataFrame(output)


def build_driver_table(ui, anomaly_index=0, branch_index=0):
    branches = get_driver_branches(ui, anomaly_index=anomaly_index)

    if not branches:
        return None

    if branch_index >= len(branches):
        return None

    rows = branches[branch_index].get("rows", [])
    if not rows:
        return None

    return pd.DataFrame(rows)