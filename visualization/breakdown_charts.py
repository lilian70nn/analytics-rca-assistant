import plotly.express as px
import pandas as pd


def plot_breakdown_bar(ui):
    data = ui.get("bar_chart", [])

    if not data:
        return None

    df = pd.DataFrame(data)

    fig = px.bar(
        df,
        x="segment",
        y="value",
        title="Breakdown by Segment"
    )

    fig.update_layout(
        xaxis_title="Segment",
        yaxis_title="Value"
    )

    return fig


def build_breakdown_table(ui):
    rows = ui.get("table_rows", [])

    if not rows:
        return None

    return pd.DataFrame(rows)