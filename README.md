# AI Analytics RCA Assistant

A modular analytics platform for investigating, visualizing, and explaining changes in business metrics.

This project implements an **AI-powered Root Cause Analysis (RCA) system** for analytics data.  
Users can ask natural language questions about metrics (e.g., revenue, sessions), and the system automatically detects anomalies, identifies drivers, and generates explanations with charts and tables.

The system combines **data analysis pipelines, anomaly detection, and LLM-based query parsing** with an interactive **Streamlit dashboard**.


# What is Root Cause Analysis (RCA)?

Root Cause Analysis aims to answer:

**Why did a metric change?**

Instead of only detecting that revenue dropped, the system decomposes the metric and identifies which components and dimensions caused the change.

Example:

Revenue drop detected on 2016-08-21

Metric decomposition:

Revenue = Sessions × Conversion Rate × AOV

Primary driver:

Sessions decreased significantly.

Top contributing segments:

- Desktop traffic
- Chrome browser users
- "(not set)" campaign


# Features

## Natural Language Queries

Users can ask questions such as:

Explain the anomalies between July and September 2016  
Why did revenue drop last month?  
Show the trend of sessions  
Break down revenue by country  

The system automatically determines the correct analysis type.


## Anomaly Investigation

Detects significant metric changes and identifies root causes.

Outputs include:

- anomaly summary  
- metric decomposition  
- top dimensions  
- root cause drivers  


## Trend Analysis

Visualizes how metrics evolve over time.

Outputs:

- summary cards  
- time-series charts  


## Breakdown Analysis

Analyzes how metrics vary across dimensions.

Outputs:

- bar charts  
- detailed tables  


## Interactive Dashboard

Built with **Streamlit**, allowing users to:

- explore anomaly events  
- select specific dates  
- inspect driver tables  
- visualize metric changes  


# System Architecture

User Question  
↓  
Query Parser (LLM)  
↓  
Analysis Engine  

- Anomaly Investigation  
- Trend Analysis  
- Breakdown Analysis  

↓  
Report Builder  
↓  
UI Builder  
↓  
Streamlit Dashboard  


# Directory Structure

````markdown
## Project Structure

```text
app/                  # Application entrypoints
  answer_question.py
  streamlit_app.py

analytics_rca/        # Core analytics logic
  analysis/
  engine/

nlp/                  # Natural language query parsing
  query_parser.py

reporting/            # Report / UI schema generation
  report_builder.py
  ui_builder.py

visualization/        # Charts and investigation views
  trend_charts.py
  breakdown_charts.py
  investigation_views.py

data/                 # Data access layer
  loader.py

utils/                # Shared utilities
  utils.py
```


# Installation

Clone the repository

git clone <repo-url>  
cd "Merchandise Sales Analysis"

Create virtual environment (optional)

python3 -m venv venv  
source venv/bin/activate

Install dependencies

pip install -r requirements.txt

If requirements.txt is missing:

pip install streamlit pandas numpy plotly scikit-learn


# Running the App

Start the Streamlit dashboard:

streamlit run app/streamlit_app.py

Open the browser interface and ask questions about your data.


# Example Workflow

1. Launch the Streamlit app.
2. Ask a question:

Explain the anomalies and main drivers between 2016-07-01 and 2016-09-01

3. The system will:

- detect anomalies
- decompose the metric
- identify dimension drivers
- generate explanation text
- display charts and tables


# Tech Stack

Python  
Pandas  
BigQuery  
Streamlit  
Plotly  
LLM (query parsing and explanation)


# Project Goal

This project demonstrates how **AI and analytics pipelines** can be combined to build an intelligent assistant that helps analysts quickly understand **why metrics change**.# analytics-rca-assistant
