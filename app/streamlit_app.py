import pandas as pd
import streamlit as st
from data.loader import get_bq_client
from app.answer_question import answer_question

from visualization.trend_charts import plot_trend_line
from visualization.breakdown_charts import (
    plot_breakdown_bar,
    build_breakdown_table,
)
from visualization.investigation_views import (
    plot_decomposition_chart,
    build_dimension_table,
    build_driver_table,
)


st.set_page_config(
    page_title="Analytics RCA Assistant",
    layout="wide"
)


@st.cache_resource
def init_client():
    return get_bq_client(
        project_id="analytics-demo-489518",
        credentials_path="credentials.json",
    )

def render_summary_cards(cards):
    if not cards:
        return

    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        label = card.get("label", "")
        value = card.get("value", "")
        date = card.get("date")
        segment = card.get("segment")

        with col:
            st.metric(label=label, value=value)
            if date:
                st.caption(f"Date: {date}")
            if segment:
                st.caption(f"Segment: {segment}")



def format_driver_option(card):
    date = card.get("date")
    direction = card.get("direction")
    driver_metric = card.get("driver_metric")
    return f"{date} | {direction} | {driver_metric}"


def build_investigation_summary_df(cards):
    if not cards:
        return pd.DataFrame()

    rows = []
    for card in cards:
        rows.append({
            "date": card.get("date"),
            "direction": card.get("direction"),
            "metric_value": round(card.get("metric_value", 0), 2) if card.get("metric_value") is not None else None,
            "z_score": round(card.get("z_score", 0), 2) if card.get("z_score") is not None else None,
            "driver_metric": card.get("driver_metric"),
            "diagnosis_type": card.get("diagnosis_type"),
        })

    return pd.DataFrame(rows)


def main():
    st.title("Analytics RCA Assistant")

    st.write("Ask a question about anomalies, trends, or breakdowns.")

    default_question = "Explain the anomalies and the main drivers from 2016-07-01 to 2016-09-01"
    question = st.text_input("Question", value=default_question)

    client = init_client()

    if "answer" not in st.session_state:
        st.session_state.answer = None

    if st.button("Run Analysis", type="primary"):
        with st.spinner("Running analysis..."):
            st.session_state.answer = answer_question(question, client)

    answer = st.session_state.answer

    if answer is None:
        return
    
    analysis_type = answer.get("analysis_type")
    report = answer.get("report") or {}
    ui = answer.get("ui") or {}
    explanation = answer.get("explanation", "")

    st.subheader("Explanation")
    st.write(explanation)

    if analysis_type == "trend":
        st.subheader("Trend Summary")
        render_summary_cards(ui.get("summary_cards", []))

        st.subheader("Trend Chart")
        fig = plot_trend_line(ui)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trend chart available.")

    elif analysis_type == "breakdown":
        st.subheader("Breakdown Summary")
        render_summary_cards(ui.get("summary_cards", []))

        st.subheader("Breakdown Chart")
        fig = plot_breakdown_bar(ui)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No breakdown chart available.")

        st.subheader("Breakdown Table")
        table_df = build_breakdown_table(ui)
        if table_df is not None and not table_df.empty:
            st.dataframe(table_df, use_container_width=True)
        else:
            st.info("No breakdown table available.")

    elif analysis_type == "investigate":
        st.subheader("Anomaly Summary")
        summary_cards = ui.get("summary_cards", [])
        summary_df = build_investigation_summary_df(summary_cards)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        if not summary_cards:
            return

        options = list(range(len(summary_cards)))
        selected_idx = st.selectbox(
            "Select anomaly date",
            options=options,
            format_func=lambda i: format_driver_option(summary_cards[i]),
            key="selected_anomaly_idx",
        )

        st.subheader("Metric Decomposition")
        fig = plot_decomposition_chart(ui, anomaly_index=selected_idx)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No decomposition chart available.")

        st.subheader("Top Dimensions")
        dimension_df = build_dimension_table(ui, anomaly_index=selected_idx)
        if dimension_df is not None and not dimension_df.empty:
            st.dataframe(dimension_df, use_container_width=True)
        else:
            st.info("No dimension table available.")

        st.subheader("Top Drivers")
        driver_df = build_driver_table(ui, anomaly_index=selected_idx)
        if driver_df is not None and not driver_df.empty:
            st.dataframe(driver_df, use_container_width=True)
        else:
            st.info("No driver table available.")

    else:
        st.error("Unsupported analysis type.")


if __name__ == "__main__":
    main()