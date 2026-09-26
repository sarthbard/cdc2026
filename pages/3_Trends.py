"""How complaint volume and outcomes move over time and across dimensions."""

from __future__ import annotations

import streamlit as st

from src import charts, queries, ui
from src.config import DIMENSIONS, label

ui.setup("Trends")
st.title("Trends")

if not ui.require_db():
    st.stop()

f = ui.sidebar_filters("tr_")

if queries.total(f) == 0:
    st.info("No complaints match these filters.")
    st.stop()

st.subheader("Volume over time")
split = st.selectbox(
    "Split the line by",
    ["(nothing)"] + DIMENSIONS,
    format_func=lambda c: "No split — total volume" if c == "(nothing)" else label(c),
)
column = None if split == "(nothing)" else split

monthly = queries.count_by_month(f, column)
title = "Complaints per month" + (f", by {label(column).lower()}" if column else "")
ui.with_table(charts.timeseries(monthly, color=column, title=title), monthly, "Monthly counts")

if column:
    st.caption(
        "Only the eight largest categories are drawn; the rest are folded into "
        "**Other** rather than given their own colors."
    )

st.divider()

st.subheader("Outcomes by dimension")
cols = st.columns(2)
with cols[0]:
    row_dim = st.selectbox(
        "Break out", ["company", "product", "issue", "state", "submitted_via"],
        format_func=label,
    )
with cols[1]:
    col_dim = st.selectbox(
        "Compare", ["company_response", "timely_response", "consumer_disputed", "submitted_via"],
        format_func=label,
    )

table = queries.cross_tab(f, row_dim, col_dim, top_rows=10)
if table.empty:
    st.info("Nothing to compare for this combination.")
else:
    ui.with_table(
        charts.share_bar(
            table, row_dim, col_dim,
            title=f"{label(col_dim)} share, top 10 by {label(row_dim).lower()}",
        ),
        table,
        "Counts behind the shares",
    )
    st.caption(
        "Shares, not volume — a company with 200 complaints and one with 200,000 "
        "occupy the same bar width here. Check the counts table before comparing."
    )
