"""SQLite access layer.

One cached read-only connection per Streamlit session, plus small helpers so
pages never build a connection themselves.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Sequence

import pandas as pd
import streamlit as st

from .config import DB_PATH, PROJECT_ROOT, TABLE

SCHEMA_PATH = PROJECT_ROOT / "src" / "schema.sql"

# Statements that may not appear in a SQL Lab query.
_FORBIDDEN = {
    "insert", "update", "delete", "drop", "alter", "create", "replace",
    "attach", "detach", "pragma", "vacuum", "reindex", "begin", "commit",
}


def db_exists() -> bool:
    return DB_PATH.exists() and DB_PATH.stat().st_size > 0


@st.cache_resource(show_spinner=False)
def get_connection() -> sqlite3.Connection:
    """Read-only connection, shared across reruns."""
    if not db_exists():
        raise FileNotFoundError(
            f"No database at {DB_PATH}. Run `python -m src.ingest --sample` first."
        )
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_write_connection() -> sqlite3.Connection:
    """Writable connection — for ingest only, never for the app pages."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")
    return conn


@st.cache_data(ttl=600, show_spinner="Querying…")
def query(sql: str, params: Sequence[Any] | None = None) -> pd.DataFrame:
    """Run a SELECT and return a DataFrame. Results are cached per (sql, params)."""
    conn = get_connection()
    return pd.read_sql_query(sql, conn, params=tuple(params or ()))


def scalar(sql: str, params: Sequence[Any] | None = None, default: Any = 0) -> Any:
    df = query(sql, params)
    if df.empty:
        return default
    value = df.iat[0, 0]
    return default if pd.isna(value) else value


def is_read_only(sql: str) -> tuple[bool, str]:
    """Cheap guard for the SQL Lab. Not a security boundary — the connection
    is already opened read-only; this just gives a friendlier error."""
    stripped = "\n".join(
        line for line in sql.splitlines() if not line.strip().startswith("--")
    ).strip().rstrip(";")
    if not stripped:
        return False, "Query is empty."
    if ";" in stripped:
        return False, "Run one statement at a time."
    first = stripped.split(None, 1)[0].lower()
    if first in _FORBIDDEN:
        return False, f"`{first.upper()}` is not allowed — this database is read-only."
    if first not in {"select", "with"}:
        return False, "Only SELECT (or WITH … SELECT) queries are allowed."
    return True, ""


@st.cache_data(ttl=3600, show_spinner=False)
def table_info() -> pd.DataFrame:
    """Column names and types, for the schema panel in the SQL Lab."""
    return query(f"PRAGMA table_info({TABLE})")


@st.cache_data(ttl=3600, show_spinner=False)
def distinct_values(column: str, limit: int = 500) -> list[str]:
    """Distinct non-null values for a dimension, most common first."""
    sql = f"""
        SELECT {column} AS v, COUNT(*) AS n
        FROM {TABLE}
        WHERE {column} IS NOT NULL AND {column} != ''
        GROUP BY {column}
        ORDER BY n DESC
        LIMIT ?
    """
    return query(sql, (limit,))["v"].tolist()


@st.cache_data(ttl=3600, show_spinner=False)
def date_bounds() -> tuple[str | None, str | None]:
    df = query(
        f"SELECT MIN(date_received) AS lo, MAX(date_received) AS hi FROM {TABLE}"
    )
    if df.empty:
        return None, None
    return df.at[0, "lo"], df.at[0, "hi"]
