"""Shared Streamlit UI pieces: page setup, the sidebar filter bar, stat tiles."""

from __future__ import annotations

import datetime as dt

import streamlit as st

from . import db, theme
from .config import DB_PATH
from .queries import Filters

PAGE_ICON = "📋"


def setup(title: str) -> None:
    """Page config + template registration. First call in every page."""
    st.set_page_config(
        page_title=f"{title} · CFPB Complaints",
        page_icon=PAGE_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    theme.register_template()


def require_db() -> bool:
    """Show a setup message instead of a stack trace when there's no database."""
    if db.db_exists():
        return True
    st.warning("No database loaded yet.", icon="⚠️")
    st.markdown(
        f"""
Build one before using this page:

```bash
# quick start — synthetic rows, runs in seconds
python -m src.ingest --sample

# the real thing — downloads ~1 GB from consumerfinance.gov
python -m src.ingest --download

# or point at a CSV you already have
python -m src.ingest --csv data/raw/complaints.csv
```

The database is written to `{DB_PATH.relative_to(DB_PATH.parent.parent)}`.
"""
    )
    return False


def sidebar_filters(key_prefix: str = "") -> Filters:
    """Render the shared filter controls and return the resulting Filters."""
    lo, hi = db.date_bounds()
    lo_date = _parse(lo) or dt.date(2011, 12, 1)
    hi_date = _parse(hi) or dt.date.today()

    with st.sidebar:
        st.subheader("Filters")

        chosen = st.date_input(
            "Date received",
            value=(lo_date, hi_date),
            min_value=lo_date,
            max_value=hi_date,
            key=f"{key_prefix}dates",
        )
        if isinstance(chosen, tuple) and len(chosen) == 2:
            date_from, date_to = chosen[0].isoformat(), chosen[1].isoformat()
        else:
            date_from, date_to = lo, hi

        products = st.multiselect(
            "Product", db.distinct_values("product"), key=f"{key_prefix}product"
        )
        issues = st.multiselect(
            "Issue", db.distinct_values("issue", limit=300), key=f"{key_prefix}issue"
        )
        companies = st.multiselect(
            "Company", db.distinct_values("company", limit=300), key=f"{key_prefix}company"
        )
        states = st.multiselect(
            "State", db.distinct_values("state", limit=60), key=f"{key_prefix}state"
        )

        with st.expander("More"):
            responses = st.multiselect(
                "Company response", db.distinct_values("company_response"),
                key=f"{key_prefix}response",
            )
            channels = st.multiselect(
                "Submitted via", db.distinct_values("submitted_via"),
                key=f"{key_prefix}channel",
            )
            narrative_only = st.checkbox(
                "Only complaints with a narrative", key=f"{key_prefix}narr"
            )
            search = st.text_input(
                "Narrative contains", placeholder="e.g. overdraft",
                key=f"{key_prefix}search",
            )

        st.caption("Filters apply to every chart and table on this page.")

    return Filters(
        date_from=date_from,
        date_to=date_to,
        products=products,
        states=states,
        companies=companies,
        issues=issues,
        responses=responses,
        channels=channels,
        narrative_only=narrative_only,
        search=search,
    )


def stat_tiles(tiles: list[tuple[str, str, str | None]]) -> None:
    """A row of headline numbers: (label, value, help-or-delta caption)."""
    cols = st.columns(len(tiles))
    for col, (name, value, note) in zip(cols, tiles):
        with col:
            st.metric(name, value)
            if note:
                st.caption(note)


def chart(fig, **kwargs) -> None:
    """Render a Plotly figure with the app's defaults."""
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False}, **kwargs)


def with_table(fig, data, caption: str = "Show the numbers") -> None:
    """Chart plus the table view behind it — identity is never color-alone."""
    chart(fig)
    with st.expander(caption):
        st.dataframe(data, use_container_width=True, hide_index=True)


def _parse(value: str | None) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None
