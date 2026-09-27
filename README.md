# Consumer Complaint Explorer — CDC 2026 (business track)

A Streamlit + SQLite app over the [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/#download-the-data).
This is the scaffold: the data pipeline, the query layer, the chart system and
four working pages. The analysis goes on top.

## Quick start

```bash
pip install -r requirements.txt

# 30k synthetic rows so the app runs immediately
python -m src.ingest --sample

streamlit run app.py
```

Then swap in the real data when you're ready:

```bash
python -m src.ingest --download                      # ~1 GB zip from the CFPB
python -m src.ingest --csv data/raw/complaints.csv   # a CSV you already have
python -m src.ingest --csv "CDC_2026_data.zip\CDC 2026\cleaned_complaints.csv"
python -m src.ingest --csv data/raw/complaints.csv --limit 500000   # a slice
```

`--download` caches the zip in `data/raw/` so a rerun doesn't re-fetch it.
`--csv` also accepts a CSV nested inside a ZIP archive. Ingest **drops and
rebuilds** `data/complaints.db` each time.

## Layout

```
app.py                  landing page — dataset summary, nav
pages/
  1_Overview.py         headline numbers, volume over time, top products/companies/states
  2_Explorer.py         filter to a slice, page the raw rows, read narratives
  3_Trends.py           volume over time split by a dimension; outcome shares
  4_SQL_Lab.py          write SQL, chart the result, download it
src/
  config.py             paths, CFPB→snake_case column map, dimension list
  schema.sql            table + indexes
  ingest.py             CSV → SQLite loader (chunked; indexes built after load)
  db.py                 cached read-only connection, query helpers
  queries.py            the Filters model and every aggregate query
  charts.py             chart builders (timeseries, ranked_bar, share_bar, state_map)
  theme.py              palette + Plotly template
  ui.py                 page setup, sidebar filters, stat tiles
data/                   gitignored — the DB and raw downloads live here
```

## The data

One row per complaint, 2011-12 to present. Columns after ingest:

| Column | Notes |
|---|---|
| `complaint_id` | primary key |
| `date_received`, `date_sent_to_company` | ISO `YYYY-MM-DD` |
| `month` | derived `YYYY-MM-01`, indexed — group on this, not on `date_received` |
| `product`, `sub_product` | what the complaint is about |
| `issue`, `sub_issue` | what went wrong |
| `company`, `state`, `zip_code` | who received it, where from |
| `narrative` | free text, present on ~1 in 3 rows (only with consumer consent) |
| `company_response`, `company_public_response` | outcome |
| `timely_response`, `consumer_disputed` | `Yes` / `No` |
| `submitted_via` | Web, Phone, Referral, … |
| `tags` | `Older American`, `Servicemember`, or blank |

Caveats worth stating in the writeup:

- Complaint counts are **not** a clean quality signal. They track company size,
  customer base, and how visible the CFPB is to a given population.
- State counts are raw — normalize by population before comparing.
- `consumer_disputed` was discontinued in 2017; it's blank on newer rows.
- The three credit bureaus dominate volume. Consider excluding or faceting them
  so they don't swamp everything else.

## Extending it

Add an aggregate to `src/queries.py` (it takes a `Filters` and returns a
DataFrame), a chart form to `src/charts.py`, then wire them together in a page.
Pages should stay thin.

Chart rules baked into `theme.py` — keep them when you add charts:

- Categorical hues are assigned in fixed slot order and never cycled; a 9th
  series folds into **Other** via `theme.fold_to_other()`.
- A chart ranked by size encodes magnitude, so it uses **one** hue, not eight.
- Never a second y-axis. Two measures of different scale = two charts.
- Every chart ships with its table view (`ui.with_table`) — three of the
  categorical hues sit under 3:1 contrast on this surface, and the table is
  what makes that legal.

The theme is pinned to light in `.streamlit/config.toml` because the palette is
validated against that surface. Adding dark mode means picking new dark steps,
not flipping the light ones.
