"""CDC 2026 — Business track.

Entry point. Run with:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from src import db, ui
from src.config import DB_PATH
from src.queries import dataset_summary

ui.setup("Home")

st.title("Consumer Complaint Explorer")
st.caption(
    "CFPB Consumer Complaint Database · Carolina Data Challenge 2026 · business track"
)

st.markdown(
    """
Complaints consumers filed against financial companies, as published by the
Consumer Financial Protection Bureau. Each row is one complaint: what product
it was about, what went wrong, which company received it, and how that company
responded.

**Source** — [consumerfinance.gov/data-research/consumer-complaints](https://www.consumerfinance.gov/data-research/consumer-complaints/#download-the-data)
"""
)

st.divider()

if db.db_exists():
    summary = dataset_summary()
    ui.stat_tiles(
        [
            ("Complaints", f"{int(summary.get('rows', 0)):,}", "rows loaded"),
            ("Companies", f"{int(summary.get('companies', 0)):,}", "named in the data"),
            ("Products", f"{int(summary.get('products', 0)):,}", "top-level categories"),
        ]
    )
    st.caption(
        f"Date range: **{summary.get('first_date')} → {summary.get('last_date')}** · "
        f"database at `{DB_PATH.name}`"
    )

    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("Pages")
        st.markdown(
            """
- **Overview** — headline numbers, volume over time, the biggest products,
  companies and states.
- **Explorer** — filter down to a slice and read the raw complaint rows.
- **Trends** — how a dimension moves over time, and how outcomes differ across
  companies and products.
"""
        )
    with right:
        st.subheader("Where the code lives")
        st.markdown(
            """
| File | What it holds |
|---|---|
| `src/ingest.py` | CSV → SQLite loader |
| `src/schema.sql` | table + indexes |
| `src/queries.py` | the filter model and every aggregate query |
| `src/charts.py` | chart builders |
| `src/theme.py` | palette and Plotly template |
| `src/ui.py` | sidebar filters, stat tiles |

Add analysis to `queries.py` and a chart form to `charts.py`; pages should stay
thin.
"""
        )
else:
    ui.require_db()

st.divider()
st.caption("Built with Streamlit · SQLite · Plotly")
