from nlp.query_parser import parse_query_llm
from analytics_rca.analysis.investigation_engine import run_investigation
from analytics_rca.analysis.trend_analysis import run_trend_analysis
from analytics_rca.analysis.breakdown_analysis import run_breakdown_analysis
from reporting.explainer import explain_analysis
from reporting.report_builder import (
    build_investigation_report,
    build_trend_report,
    build_breakdown_report,
)
from reporting.ui_builder import (
    build_investigation_ui,
    build_trend_ui,
    build_breakdown_ui,
)

# from reporting.report_builder import build_investigation_report
# from reporting.ui_builder import build_investigation_ui



def answer_question(question, client):

    parsed = parse_query_llm(question)

    intent = parsed["intent"]
    metric = parsed["metric"]
    dimension = parsed["dimension"]
    if dimension == "null":
        dimension = None
    start_date = parsed["start_date"]
    end_date = parsed["end_date"]

    report = None
    ui = None


    # investigate
    if intent == "investigate":

        result = run_investigation(
            client,
            start_date=start_date,
            end_date=end_date,
            metric=metric
        )

        report = build_investigation_report(result)
        ui = build_investigation_ui(report)

    # trend
    elif intent == "trend":

        result = run_trend_analysis(
            client,
            start_date=start_date,
            end_date=end_date,
            metric=metric
        )

        report = build_trend_report(result)
        ui = build_trend_ui(report)
    # breakdown
    elif intent == "breakdown":

        result = run_breakdown_analysis(
            client,
            start_date=start_date,
            end_date=end_date,
            metric=metric,
            dimension=dimension
        )

        report = build_breakdown_report(result)
        ui = build_breakdown_ui(report)

    else:

        result = {"error": "unknown intent"}

    explanation = explain_analysis(question, intent, result)

    return {
        "question": question,
        "parsed_query": parsed,
        "analysis_type": intent,
        "result": result,
        "report": report,
        "ui": ui,
        "explanation": explanation
    }