"""Build the SQLite database from the CFPB Consumer Complaint CSV.

    python -m src.ingest --sample                # synthetic rows, for development
    python -m src.ingest --download              # fetch + load the real bulk CSV
    python -m src.ingest --csv path/to/file.csv  # load a CSV you already have
    python -m src.ingest --csv file.csv --limit 200000   # load a slice

Source: https://www.consumerfinance.gov/data-research/consumer-complaints/
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile

import pandas as pd

from .config import (
    CFPB_CSV_ZIP_URL,
    COLUMN_MAP,
    COLUMNS,
    DATA_DIR,
    DB_PATH,
    RAW_DIR,
    TABLE,
)
from .db import SCHEMA_PATH, get_write_connection

CHUNK_SIZE = 100_000


def _statements(kind: str) -> list[str]:
    """Split schema.sql into its CREATE TABLE vs CREATE INDEX statements.

    Indexes are built *after* the bulk insert — adding them up front makes
    loading the full 6M-row file several times slower.
    """
    lines = [
        line
        for line in SCHEMA_PATH.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith("--")
    ]
    script = "\n".join(line.split("--")[0] for line in lines)
    statements = [s.strip() for s in script.split(";") if s.strip()]
    return [s for s in statements if kind in s.upper()]


def create_table(conn) -> None:
    for statement in _statements("CREATE TABLE"):
        conn.execute(statement)
    conn.commit()


def create_indexes(conn) -> None:
    for statement in _statements("CREATE INDEX"):
        conn.execute(statement)
    conn.commit()


def normalize(chunk: pd.DataFrame) -> pd.DataFrame:
    """Rename CFPB headers, coerce dates, derive the month grouping key."""
    chunk = chunk.rename(columns=COLUMN_MAP)
    for column in COLUMNS:
        if column not in chunk.columns:
            chunk[column] = None
    chunk = chunk[COLUMNS].copy()

    received = pd.to_datetime(chunk["date_received"], errors="coerce", format="mixed")
    chunk["date_received"] = received.dt.strftime("%Y-%m-%d")
    chunk["month"] = received.dt.strftime("%Y-%m-01")
    chunk["date_sent_to_company"] = pd.to_datetime(
        chunk["date_sent_to_company"], errors="coerce", format="mixed"
    ).dt.strftime("%Y-%m-%d")

    chunk["complaint_id"] = pd.to_numeric(chunk["complaint_id"], errors="coerce")
    chunk = chunk.dropna(subset=["complaint_id"])
    chunk["complaint_id"] = chunk["complaint_id"].astype("int64")

    for column in ("product", "company", "state", "issue"):
        chunk[column] = chunk[column].astype("string").str.strip()

    return chunk


def load_csv(source, limit: int | None = None) -> int:
    """Stream a CSV into SQLite in chunks. Returns the number of rows written."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = get_write_connection()
    create_table(conn)

    written = 0
    reader = pd.read_csv(
        source,
        chunksize=CHUNK_SIZE,
        dtype=str,
        keep_default_na=False,
        na_values=[""],
        on_bad_lines="warn",
    )
    for i, chunk in enumerate(reader, start=1):
        if limit is not None and written >= limit:
            break
        if limit is not None:
            chunk = chunk.head(limit - written)
        frame = normalize(chunk)
        # method="multi" batches rows into one INSERT; SQLite caps a statement
        # at 999 bound variables on older builds, so size the batch by columns.
        frame.to_sql(TABLE, conn, if_exists="append", index=False, method="multi",
                     chunksize=max(1, 900 // len(frame.columns)))
        written += len(frame)
        print(f"  chunk {i}: {written:,} rows", flush=True)

    conn.commit()
    print("  building indexes…", flush=True)
    create_indexes(conn)
    conn.execute("ANALYZE")
    conn.commit()
    conn.close()
    return written


def download() -> io.BytesIO:
    """Fetch the bulk CSV zip from the CFPB (~1 GB compressed)."""
    import requests

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    local = RAW_DIR / "complaints.csv.zip"
    if not local.exists():
        print(f"Downloading {CFPB_CSV_ZIP_URL} → {local}")
        with requests.get(CFPB_CSV_ZIP_URL, stream=True, timeout=120) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0))
            done = 0
            with local.open("wb") as handle:
                for block in response.iter_content(chunk_size=1 << 20):
                    handle.write(block)
                    done += len(block)
                    if total:
                        print(f"\r  {done / total:6.1%}", end="", flush=True)
            print()
    else:
        print(f"Using cached download at {local}")

    archive = zipfile.ZipFile(local)
    name = next(n for n in archive.namelist() if n.endswith(".csv"))
    return archive.open(name)


def sample(rows: int = 25_000, seed: int = 2026) -> io.StringIO:
    """Synthetic rows shaped like the real file, so the app runs immediately."""
    import numpy as np

    rng = np.random.default_rng(seed)

    products = [
        "Credit reporting, credit repair services, or other personal consumer reports",
        "Debt collection", "Mortgage", "Credit card or prepaid card",
        "Checking or savings account", "Student loan", "Vehicle loan or lease",
        "Money transfer, virtual currency, or money service", "Payday loan, title loan, or personal loan",
    ]
    sub_products = ["Credit reporting", "General-purpose credit card", "Conventional home mortgage",
                    "Checking account", "Federal student loan servicing", "Other debt", "I do not know"]
    issues = [
        "Incorrect information on your report", "Attempts to collect debt not owed",
        "Problem with a credit reporting company's investigation",
        "Trouble during payment process", "Managing an account",
        "Improper use of your report", "Struggling to repay your loan",
        "Problem with a purchase shown on your statement", "Fees or interest",
    ]
    companies = ["EQUIFAX, INC.", "TRANSUNION INTERMEDIATE HOLDINGS, INC.",
                 "Experian Information Solutions Inc.", "BANK OF AMERICA, NATIONAL ASSOCIATION",
                 "WELLS FARGO & COMPANY", "JPMORGAN CHASE & CO.", "CITIBANK, N.A.",
                 "CAPITAL ONE FINANCIAL CORPORATION", "SYNCHRONY FINANCIAL",
                 "NAVIENT SOLUTIONS, LLC.", "PORTFOLIO RECOVERY ASSOCIATES INC", "Other"]
    states = ["CA", "TX", "FL", "NY", "GA", "PA", "IL", "NC", "OH", "NJ", "VA", "MD",
              "AZ", "MI", "TN", "WA", "MA", "SC", "CO", "IN"]
    responses = ["Closed with explanation", "Closed with non-monetary relief",
                 "Closed with monetary relief", "In progress", "Untimely response"]
    channels = ["Web", "Referral", "Phone", "Postal mail", "Fax", "Email"]

    dates = pd.to_datetime("2019-01-01") + pd.to_timedelta(
        rng.integers(0, 365 * 6, rows), unit="D"
    )
    frame = pd.DataFrame(
        {
            "Date received": dates.strftime("%Y-%m-%d"),
            "Product": rng.choice(products, rows, p=_weights(len(products), rng)),
            "Sub-product": rng.choice(sub_products, rows),
            "Issue": rng.choice(issues, rows, p=_weights(len(issues), rng)),
            "Sub-issue": rng.choice(["Information belongs to someone else", "Debt is not yours", ""], rows),
            "Consumer complaint narrative": rng.choice(
                ["", "", "", "I have repeatedly disputed this account and nothing has been corrected."], rows
            ),
            "Company public response": "",
            "Company": rng.choice(companies, rows, p=_weights(len(companies), rng)),
            "State": rng.choice(states, rows, p=_weights(len(states), rng)),
            "ZIP code": rng.integers(10000, 99999, rows).astype(str),
            "Tags": rng.choice(["", "", "", "Older American", "Servicemember"], rows),
            "Consumer consent provided?": "Consent not provided",
            "Submitted via": rng.choice(channels, rows, p=_weights(len(channels), rng)),
            "Date sent to company": (dates + pd.to_timedelta(rng.integers(0, 5, rows), unit="D")).strftime("%Y-%m-%d"),
            "Company response to consumer": rng.choice(responses, rows, p=_weights(len(responses), rng)),
            "Timely response?": rng.choice(["Yes", "No"], rows, p=[0.97, 0.03]),
            "Consumer disputed?": rng.choice(["", "Yes", "No"], rows, p=[0.8, 0.05, 0.15]),
            "Complaint ID": range(1_000_000, 1_000_000 + rows),
        }
    )
    buffer = io.StringIO()
    frame.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer


def _weights(n: int, rng) -> list[float]:
    """A skewed distribution — real complaint data is very long-tailed."""
    raw = 1 / (1 + rng.permutation(n))
    return list(raw / raw.sum())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sample", action="store_true", help="generate synthetic rows")
    group.add_argument("--download", action="store_true", help="fetch the real bulk CSV")
    group.add_argument("--csv", help="path to a CFPB complaints CSV")
    parser.add_argument("--limit", type=int, help="stop after N rows")
    parser.add_argument("--rows", type=int, default=25_000, help="rows for --sample")
    args = parser.parse_args(argv)

    if args.sample:
        source = sample(args.rows)
    elif args.download:
        source = download()
    else:
        source = args.csv

    print(f"Loading into {DB_PATH}")
    written = load_csv(source, limit=args.limit)
    size_mb = DB_PATH.stat().st_size / 1e6
    print(f"Done — {written:,} rows, {size_mb:,.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
