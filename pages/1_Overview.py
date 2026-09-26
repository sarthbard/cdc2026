"""Headline numbers and the biggest slices of the filtered data."""

from __future__ import annotations

import streamlit as st

from src import charts, queries, ui

ui.setup("Overview")
st.title("Overview")

if not ui.require_db():
    st.stop()

f = ui.sidebar_filters("ov_")

total = queries.total(f)
if total == 0:
    st.info("No complaints match these filters.")
    st.stop()

timely = queries.rate(f, "timely_response", "Yes")
disputed = queries.rate(f, "consumer_disputed", "Yes")
relief = queries.rate(f, "company_response", "Closed with monetary relief")

ui.stat_tiles(
    [
        ("Complaints", f"{total:,}", "matching the current filters"),
        ("Timely response", f"{timely:.1%}", "company replied on time"),
        ("Monetary relief", f"{relief:.1%}", "closed with money back"),
        ("Consumer disputed", f"{disputed:.1%}", "of complaints with a dispute flag"),
    ]
)

st.divider()

monthly = queries.count_by_month(f)
ui.with_table(
    charts.timeseries(monthly, title="Complaint volume by month"),
    monthly,
    "Monthly counts",
)

st.divider()

left, right = st.columns(2)
with left:
    products = queries.count_by(f, "product", limit=25)
    ui.with_table(
        charts.ranked_bar(products, "product", title="Top products"),
        products,
        "Product counts",
    )
with right:
    issues = queries.count_by(f, "issue", limit=25)
    ui.with_table(
        charts.ranked_bar(issues, "issue", title="Top issues"),
        issues,
        "Issue counts",
    )

st.divider()

left, right = st.columns(2)
with left:
    companies = queries.count_by(f, "company", limit=25)
    ui.with_table(
        charts.ranked_bar(companies, "company", title="Companies receiving the most complaints"),
        companies,
        "Company counts",
    )
with right:
    states = queries.count_by(f, "state", limit=60)
    ui.with_table(
        charts.state_map(states, title="Complaints by state"),
        states,
        "State counts",
    )
    st.caption(
        "Raw counts, not per-capita — big states lead because they are big. "
        "Normalize by population before drawing a conclusion."
    )
