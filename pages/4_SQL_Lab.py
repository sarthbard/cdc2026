"""Write SQL against the complaints database, chart the result, download it."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src import charts, db, ui
from src.config import TABLE

ui.setup("SQL Lab")
st.title("SQL Lab")
st.caption(f"Read-only queries against `{TABLE}`. One statement at a time.")

if not ui.require_db():
    st.stop()

EXAMPLES = {
    "Top companies": f"""
SELECT company, COUNT(*) AS n
FROM {TABLE}
GROUP BY company
ORDER BY n DESC
LIMIT 15
""".strip(),
    "Monthly volume": f"""
SELECT month, COUNT(*) AS n
FROM {TABLE}
WHERE month >= '2022-01-01'
GROUP BY month
ORDER BY month
""".strip(),
    "Timely-response rate by product": f"""
SELECT product,
       COUNT(*) AS n,
       ROUND(100.0 * SUM(CASE WHEN timely_response = 'Yes' THEN 1 ELSE 0 END)
             / COUNT(*), 1) AS timely_pct
FROM {TABLE}
WHERE product IS NOT NULL AND product != ''
GROUP BY product
HAVING n >= 100
ORDER BY timely_pct ASC
""".strip(),
    "Monetary relief rate, big companies only": f"""
SELECT company,
       COUNT(*) AS n,
       ROUND(100.0 * SUM(CASE WHEN company_response = 'Closed with monetary relief'
                              THEN 1 ELSE 0 END) / COUNT(*), 2) AS relief_pct
FROM {TABLE}
GROUP BY company
HAVING n >= 1000
ORDER BY relief_pct DESC
LIMIT 20
""".strip(),
    "Year-over-year change by product": f"""
WITH yearly AS (
    SELECT product, substr(date_received, 1, 4) AS yr, COUNT(*) AS n
    FROM {TABLE}
    GROUP BY product, yr
)
SELECT product, yr, n,
       n - LAG(n) OVER (PARTITION BY product ORDER BY yr) AS change
FROM yearly
ORDER BY product, yr
""".strip(),
}

with st.sidebar:
    st.subheader("Schema")
    info = db.table_info()
    st.dataframe(
        info[["name", "type"]], use_container_width=True, hide_index=True, height=440
    )

example = st.selectbox("Start from an example", list(EXAMPLES))
sql = st.text_area("Query", value=EXAMPLES[example], height=240, key=f"sql_{example}")

run = st.button("Run query", type="primary")

if run:
    ok, problem = db.is_read_only(sql)
    if not ok:
        st.error(problem)
        st.stop()
    try:
        result = db.query(sql.strip().rstrip(";"))
    except Exception as error:  # surface SQLite's message, don't crash the page
        st.error(f"SQLite: {error}")
        st.stop()

    st.session_state["sql_result"] = result

result: pd.DataFrame | None = st.session_state.get("sql_result")

if result is not None:
    st.success(f"{len(result):,} rows")
    st.dataframe(result, use_container_width=True, hide_index=True)
    st.download_button(
        "Download CSV",
        result.to_csv(index=False).encode("utf-8"),
        file_name="query_result.csv",
        mime="text/csv",
    )

    numeric = [c for c in result.columns if pd.api.types.is_numeric_dtype(result[c])]
    categorical = [c for c in result.columns if c not in numeric]

    if numeric and categorical:
        st.divider()
        st.subheader("Chart it")
        cols = st.columns(3)
        with cols[0]:
            form = st.radio("Form", ["Bar", "Line"], horizontal=True)
        with cols[1]:
            dimension = st.selectbox("Category / x-axis", categorical)
        with cols[2]:
            measure = st.selectbox("Value", numeric)

        plot = result[[dimension, measure]].rename(columns={measure: "n"})
        if form == "Bar":
            ui.chart(charts.ranked_bar(plot, dimension, title=f"{measure} by {dimension}", top=20))
        else:
            ui.chart(charts.timeseries(plot, x=dimension, title=f"{measure} over {dimension}"))
