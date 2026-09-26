-- Schema for the CFPB Consumer Complaint Database extract.
-- Everything is TEXT except the id, because the source CSV is entirely
-- strings. Cast at query time where you need numbers.

CREATE TABLE IF NOT EXISTS complaints (
    complaint_id            INTEGER PRIMARY KEY,
    date_received           TEXT,      -- ISO: YYYY-MM-DD
    month                   TEXT,      -- derived: YYYY-MM-01, for fast grouping
    product                 TEXT,
    sub_product             TEXT,
    issue                   TEXT,
    sub_issue               TEXT,
    narrative               TEXT,
    company_public_response TEXT,
    company                 TEXT,
    state                   TEXT,
    zip_code                TEXT,
    tags                    TEXT,
    consumer_consent        TEXT,
    submitted_via           TEXT,
    date_sent_to_company    TEXT,
    company_response        TEXT,
    timely_response         TEXT,
    consumer_disputed       TEXT
);

CREATE INDEX IF NOT EXISTS idx_complaints_date     ON complaints (date_received);
CREATE INDEX IF NOT EXISTS idx_complaints_month    ON complaints (month);
CREATE INDEX IF NOT EXISTS idx_complaints_product  ON complaints (product);
CREATE INDEX IF NOT EXISTS idx_complaints_company  ON complaints (company);
CREATE INDEX IF NOT EXISTS idx_complaints_state    ON complaints (state);
CREATE INDEX IF NOT EXISTS idx_complaints_issue    ON complaints (issue);
CREATE INDEX IF NOT EXISTS idx_complaints_response ON complaints (company_response);
