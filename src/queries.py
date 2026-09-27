"""Filter model and the named queries the pages run.

Every page builds a :class:`Filters`, turns it into a WHERE clause once, and
passes it to the query helpers below. Add new analysis here, not in the pages.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from . import db
from .config import TABLE


@dataclass
class Filters:
    """The sidebar state. Empty list / None means "no filter on this field"."""

    date_from: str | None = None
    date_to: str | None = None
    products: list[str] = field(default_factory=list)
    states: list[str] = field(default_factory=list)
    companies: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    responses: list[str] = field(default_factory=list)
    channels: list[str] = field(default_factory=list)
    narrative_only: bool = False
    search: str = ""

    def where(self) -> tuple[str, list]:
        """Return a ``WHERE …`` fragment (or empty string) and its params."""
        clauses: list[str] = []
        params: list = []

        def add_in(column: str, values: list[str]) -> None:
            if values:
                clauses.append(f"{column} IN ({','.join('?' * len(values))})")
                params.extend(values)

        if self.date_from:
            clauses.append("date_received >= ?")
            params.append(self.date_from)
        if self.date_to:
            clauses.append("date_received <= ?")
            params.append(self.date_to)

        add_in("product", self.products)
        add_in("state", self.states)
        add_in("company", self.companies)
        add_in("issue", self.issues)
        add_in("company_response", self.responses)
        add_in("submitted_via", self.channels)

        if self.narrative_only:
            clauses.append("narrative IS NOT NULL AND narrative != ''")
        if self.search.strip():
            clauses.append("narrative LIKE ?")
            params.append(f"%{self.search.strip()}%")

        if not clauses:
            return "", []
        return "WHERE " + "\n  AND ".join(clauses), params

    def key(self) -> tuple:
        """Hashable identity, so Streamlit can cache on it."""
        sql, params = self.where()
        return (sql, tuple(params))


# --- Aggregates -----------------------------------------------------------


def total(f: Filters) -> int:
    where, params = f.where()
    return int(db.scalar(f"SELECT COUNT(*) FROM {TABLE} {where}", params))


def count_by(f: Filters, column: str, limit: int = 50) -> pd.DataFrame:
    """Complaint counts per value of ``column``, largest first."""
    where, params = f.where()
    gate = "WHERE" if not where else "AND"
    sql = f"""
        SELECT {column} AS {column}, COUNT(*) AS n
        FROM {TABLE}
        {where}
        {gate} {column} IS NOT NULL AND {column} != ''
        GROUP BY {column}
        ORDER BY n DESC
        LIMIT ?
    """
    return db.query(sql, params + [limit])


def count_by_month(f: Filters, column: str | None = None, limit: int = 8) -> pd.DataFrame:
    """Monthly complaint counts, optionally split by a dimension."""
    where, params = f.where()
    if column is None:
        sql = f"""
            SELECT month, COUNT(*) AS n
            FROM {TABLE}
            {where}
            GROUP BY month
            ORDER BY month
        """
        return db.query(sql, params)

    gate = "WHERE" if not where else "AND"
    sql = f"""
        WITH top AS (
            SELECT {column} AS k
            FROM {TABLE}
            {where}
            {gate} {column} IS NOT NULL AND {column} != ''
            GROUP BY {column}
            ORDER BY COUNT(*) DESC
            LIMIT ?
        )
        SELECT month, {column} AS {column}, COUNT(*) AS n
        FROM {TABLE}
        {where}
        {gate} {column} IN (SELECT k FROM top)
        GROUP BY month, {column}
        ORDER BY month
    """
    return db.query(sql, params + [limit] + params)


def cross_tab(f: Filters, row: str, col: str, top_rows: int = 10) -> pd.DataFrame:
    """Counts for the top ``top_rows`` values of ``row``, broken out by ``col``."""
    where, params = f.where()
    gate = "WHERE" if not where else "AND"
    sql = f"""
        WITH top AS (
            SELECT {row} AS k
            FROM {TABLE}
            {where}
            {gate} {row} IS NOT NULL AND {row} != ''
            GROUP BY {row}
            ORDER BY COUNT(*) DESC
            LIMIT ?
        )
        SELECT {row} AS {row}, {col} AS {col}, COUNT(*) AS n
        FROM {TABLE}
        {where}
        {gate} {row} IN (SELECT k FROM top)
          AND {col} IS NOT NULL AND {col} != ''
        GROUP BY {row}, {col}
    """
    return db.query(sql, params + [top_rows] + params)


def rate(f: Filters, column: str, value: str) -> float:
    """Share of filtered complaints where ``column`` equals ``value`` (0–1)."""
    where, params = f.where()
    gate = "WHERE" if not where else "AND"
    sql = f"""
        SELECT AVG(CASE WHEN {column} = ? THEN 1.0 ELSE 0.0 END)
        FROM {TABLE}
        {where}
        {gate} {column} IS NOT NULL AND {column} != ''
    """
    return float(db.scalar(sql, [value] + params, default=0.0))


def rows(f: Filters, limit: int = 500, offset: int = 0, order: str = "date_received DESC") -> pd.DataFrame:
    """A page of raw complaint rows for the Explorer table."""
    where, params = f.where()
    sql = f"""
        SELECT complaint_id, date_received, product, sub_product, issue,
               company, state, submitted_via, company_response,
               timely_response, consumer_disputed, narrative
        FROM {TABLE}
        {where}
        ORDER BY {order}
        LIMIT ? OFFSET ?
    """
    return db.query(sql, params + [limit, offset])


def dataset_summary() -> dict:
    """Unfiltered facts about what's loaded — shown on the home page."""
    row = db.query(
        f"""
        SELECT COUNT(*)                        AS rows,
               MIN(date_received)              AS first_date,
               MAX(date_received)              AS last_date,
               COUNT(DISTINCT company)         AS companies,
               COUNT(DISTINCT product)         AS products,
               COUNT(DISTINCT state)           AS states
        FROM {TABLE}
        """
    )
    return row.iloc[0].to_dict() if not row.empty else {}
