"""Paths, dataset constants, and the CFPB -> SQLite column mapping."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "complaints.db"

TABLE = "complaints"

# Bulk download page: https://www.consumerfinance.gov/data-research/consumer-complaints/#download-the-data
CFPB_CSV_ZIP_URL = "https://files.consumerfinance.gov/ccdb/complaints.csv.zip"

# CFPB's CSV headers -> the snake_case names used everywhere in this app.
COLUMN_MAP = {
    "Date received": "date_received",
    "Product": "product",
    "Sub-product": "sub_product",
    "Issue": "issue",
    "Sub-issue": "sub_issue",
    "Consumer complaint narrative": "narrative",
    "Company public response": "company_public_response",
    "Company": "company",
    "State": "state",
    "ZIP code": "zip_code",
    "Tags": "tags",
    "Consumer consent provided?": "consumer_consent",
    "Submitted via": "submitted_via",
    "Date sent to company": "date_sent_to_company",
    "Company response to consumer": "company_response",
    "Timely response?": "timely_response",
    "Consumer disputed?": "consumer_disputed",
    "Complaint ID": "complaint_id",
}

COLUMNS = list(COLUMN_MAP.values())

DATE_COLUMNS = ["date_received", "date_sent_to_company"]

# Dimensions offered in the sidebar filters and the group-by pickers.
DIMENSIONS = [
    "product",
    "sub_product",
    "issue",
    "company",
    "state",
    "submitted_via",
    "company_response",
    "timely_response",
    "consumer_disputed",
]

LABELS = {
    "date_received": "Date received",
    "product": "Product",
    "sub_product": "Sub-product",
    "issue": "Issue",
    "sub_issue": "Sub-issue",
    "company": "Company",
    "state": "State",
    "submitted_via": "Submitted via",
    "company_response": "Company response",
    "timely_response": "Timely response",
    "consumer_disputed": "Consumer disputed",
    "n": "Complaints",
}


def label(column: str) -> str:
    return LABELS.get(column, column.replace("_", " ").capitalize())
