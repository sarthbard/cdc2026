"""Filter to a slice and read the underlying complaint rows."""

from __future__ import annotations

import streamlit as st

from src import queries, ui

ui.setup("Explorer")
st.title("Explorer")
st.caption("Filter on the left, then page through the matching complaints.")

if not ui.require_db():
    st.stop()

f = ui.sidebar_filters("ex_")

total = queries.total(f)
st.metric("Matching complaints", f"{total:,}")

if total == 0:
    st.info("No complaints match these filters.")
    st.stop()

controls = st.columns([2, 2, 3])
with controls[0]:
    page_size = st.selectbox("Rows per page", [50, 100, 250, 500], index=1)
with controls[1]:
    sort = st.selectbox(
        "Sort by",
        ["Newest first", "Oldest first", "Company (A→Z)", "Product (A→Z)"],
    )
with controls[2]:
    pages = max(1, -(-total // page_size))
    page = st.number_input(
        "Page", min_value=1, max_value=pages, value=1, step=1,
        help=f"{pages:,} pages at {page_size} rows each",
    )

order = {
    "Newest first": "date_received DESC, complaint_id DESC",
    "Oldest first": "date_received ASC, complaint_id ASC",
    "Company (A→Z)": "company ASC, date_received DESC",
    "Product (A→Z)": "product ASC, date_received DESC",
}[sort]

data = queries.rows(f, limit=page_size, offset=(int(page) - 1) * page_size, order=order)

st.dataframe(
    data,
    use_container_width=True,
    hide_index=True,
    column_config={
        "complaint_id": st.column_config.NumberColumn("ID", format="%d"),
        "date_received": st.column_config.TextColumn("Received", width="small"),
        "narrative": st.column_config.TextColumn("Narrative", width="large"),
    },
)

st.download_button(
    "Download this page as CSV",
    data.to_csv(index=False).encode("utf-8"),
    file_name=f"complaints_page{int(page)}.csv",
    mime="text/csv",
)

st.divider()

st.subheader("Read a narrative")
with_text = data[data["narrative"].notna() & (data["narrative"] != "")]
if with_text.empty:
    st.caption(
        "None of the rows on this page have a narrative. Turn on "
        "**Only complaints with a narrative** in the sidebar to restrict to the "
        "roughly one-in-three complaints where the consumer consented to publication."
    )
else:
    choice = st.selectbox(
        "Complaint",
        with_text["complaint_id"].tolist(),
        format_func=lambda cid: (
            f"{cid} · {with_text.loc[with_text.complaint_id == cid, 'company'].iat[0]}"
        ),
    )
    row = with_text[with_text["complaint_id"] == choice].iloc[0]
    st.caption(
        f"{row['date_received']} · {row['product']} · {row['issue']} · "
        f"{row['company']} ({row['state']}) · response: {row['company_response']}"
    )
    st.write(row["narrative"])
