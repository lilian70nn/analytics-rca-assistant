import plotly.express as px
import pandas as pd


def plot_trend_line(ui):
    data = ui.get("line_chart", [])

    if not data:
        return None

    df = pd.DataFrame(data)

    fig = px.line(
        df,
        x="date",
        y="value",
        title="Metric Trend"
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Value"
    )

    return fig