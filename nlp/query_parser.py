import json
import ollama
import re


SYSTEM_PROMPT = """
You are a query parser for an analytics investigation system.

Return ONLY valid JSON.

Schema:

{
  "intent": "trend | breakdown | investigate",
  "metric": "revenue | transactions | sessions | pageviews | bounces | time_on_site | conversion_rate | bounce_rate",
  "dimension": "country | region | city | device | operating_system | browser | source | medium | campaign | null",
  "direction": "drop | spike | null",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "raw_question": "string"
}

Intent definitions:

trend
User wants to see metric over time.

Examples:
- show revenue trend
- daily sessions
- traffic over time

breakdown
User wants metric grouped by a dimension.

Examples:
- revenue by country
- sessions by device
- traffic by source

investigate
User wants to understand WHY something changed.

Examples:
- why did revenue drop
- investigate revenue anomalies
- why did sessions spike

Direction rules:

drop → drop, decrease, decline, fall
spike → increase, rise, surge

If no direction is mentioned → direction = null

Dataset date range:

2016-08-01 → 2017-08-01

If no date is mentioned:
start_date = 2016-08-01
end_date = 2017-08-01

Return JSON only.
"""

VALID_METRICS = {
    "revenue",
    "transactions",
    "sessions",
    "pageviews",
    "bounces",
    "time_on_site",
    "conversion_rate",
    "bounce_rate",
}




def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        return json.loads(match.group())
    raise ValueError("No JSON found in model output")


def parse_query_llm(question: str):

    response = ollama.chat(
        model="qwen2.5-coder:7b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ]
    )

    content = response["message"]["content"]

    parsed = extract_json(content)
    
    metric = parsed.get("metric")

    if metric not in VALID_METRICS:
        parsed["metric"] = "revenue"


    dimension = parsed.get("dimension")

    VALID_DIMENSIONS = {
        "country", "region", "city", "device",
        "operating_system", "browser", "source",
        "medium", "campaign", None, "null"
    }

    if dimension not in VALID_DIMENSIONS:
        dimension = None
    elif dimension == "null":
        dimension = None

    parsed["dimension"] = dimension

    return parsed

