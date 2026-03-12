import os
import pandas as pd
from google.cloud import bigquery

def get_bq_client(project_id: str, credentials_path: str) -> bigquery.Client:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    return bigquery.Client(project=project_id)


# data layer
def load_fact_sessions(
    client: bigquery.Client,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:

    start_suffix = start_date.replace("-", "")
    end_suffix = end_date.replace("-", "")

    query = f"""
    SELECT
      PARSE_DATE('%Y%m%d', date) AS event_day,
      fullVisitorId AS visitor_id,

      geoNetwork.country AS country,
      geoNetwork.region AS region,
      geoNetwork.city AS city,

      device.deviceCategory AS device,
      device.operatingSystem AS operating_system,
      device.browser AS browser,

      trafficSource.source AS source,
      trafficSource.medium AS medium,
      trafficSource.campaign AS campaign,

      1 AS sessions,
      COALESCE(totals.transactions, 0) AS transactions,
      COALESCE(totals.totalTransactionRevenue, 0) / 1e6 AS revenue,
      COALESCE(totals.pageviews, 0) AS pageviews,
      COALESCE(totals.bounces, 0) AS bounces,
      COALESCE(totals.timeOnSite, 0) AS time_on_site
    FROM `bigquery-public-data.google_analytics_sample.ga_sessions_*`
    WHERE _TABLE_SUFFIX BETWEEN '{start_suffix}' AND '{end_suffix}'
    """

    df = client.query(query).to_dataframe()

    return df