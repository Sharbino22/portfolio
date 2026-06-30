-- =============================================================================
-- 00_schema.sql  -- DDL for the revenue cycle claims model
-- =============================================================================
-- Engine: SQLite. SQL kept portable (ANSI-ish); dialect notes inline.
--
-- MODEL: a small STAR SCHEMA.
--   * One FACT table  : claims_raw   (grain = ONE ROW PER CLAIM, header level)
--   * Three DIMENSIONS : dim_payer, dim_service_line, dim_denial_reason
--
-- GRAIN (locked): one row per claim. NOT per claim line, NOT per encounter.
--   Every metric is computed at claim grain, then aggregated up to
--   payer / service-line / month. Line-level detail is a known extension.
--
-- DESIGN PRINCIPLE -- permissive landing, constrained trusted layer:
--   claims_raw is the LANDING ZONE. It is intentionally loose (no PK on
--   claim_id, few NOT NULLs, negatives allowed, dates as text) so that the
--   deliberately-seeded data-quality problems (duplicate ids, missing pay
--   dates, impossible dates, negative charges) actually LOAD and can be
--   detected in Stage B. Constraints, uniqueness, and standardization are
--   enforced LATER in the cleaned staging layer (04_clean_views.sql), not here.
--
-- SQLite type notes (all defensible interview points):
--   * No native DATE type -> dates stored as TEXT in ISO-8601 'YYYY-MM-DD',
--     which sorts and compares correctly and works with date() functions.
--   * Money as NUMERIC affinity. (Real warehouse: DECIMAL(12,2) to avoid
--     binary floating-point rounding. Flagged where it matters.)
--   * FK constraints are PARSED but only ENFORCED when:  PRAGMA foreign_keys = ON;
--     (off by default in SQLite). We declare them for documentation + optional
--     enforcement on the clean layer.
-- =============================================================================

PRAGMA foreign_keys = ON;   -- opt in to FK enforcement (off by default)

-- Idempotent rebuild: drop in dependency order (fact first, then dims).
DROP TABLE IF EXISTS claims_raw;
DROP TABLE IF EXISTS dim_payer;
DROP TABLE IF EXISTS dim_service_line;
DROP TABLE IF EXISTS dim_denial_reason;

-- -----------------------------------------------------------------------------
-- DIMENSION: dim_payer
--   Canonical insurer reference. This is the CLEAN target that messy
--   claims_raw.payer_name_raw values get standardized to during cleaning.
--   payer_type is the executive-level rollup (denial/collection behavior
--   differs sharply by payer type).
-- -----------------------------------------------------------------------------
CREATE TABLE dim_payer (
    payer_id     TEXT PRIMARY KEY,            -- e.g. 'PAY001'
    payer_name   TEXT NOT NULL,               -- canonical name, e.g. 'Blue Cross Blue Shield'
    payer_type   TEXT NOT NULL                -- Commercial | Medicare | Medicaid | Self-Pay | Other
);

-- -----------------------------------------------------------------------------
-- DIMENSION: dim_service_line
--   Clinical segmentation axis. Charge-capture and coding issues cluster by
--   service line. department_group lets us roll specialties into broader groups.
-- -----------------------------------------------------------------------------
CREATE TABLE dim_service_line (
    service_line_name TEXT PRIMARY KEY,        -- e.g. 'Cardiology' (fact joins by name)
    department_group  TEXT NOT NULL            -- e.g. 'Medical' | 'Surgical' | 'Ancillary'
);

-- -----------------------------------------------------------------------------
-- DIMENSION: dim_denial_reason
--   CARC-style reason codes -> human-readable description + CATEGORY rollup.
--   The category is the analytical payload: it turns ~dozens of raw codes into
--   a story (preventable front-end vs. payer-driven).
-- -----------------------------------------------------------------------------
CREATE TABLE dim_denial_reason (
    denial_reason_code TEXT PRIMARY KEY,       -- e.g. '197'
    reason_description TEXT NOT NULL,           -- e.g. 'Authorization missing'
    reason_category    TEXT NOT NULL            -- Eligibility | Authorization | Coding |
                                                -- Medical Necessity | Timely Filing | Technical-Other
);

-- -----------------------------------------------------------------------------
-- FACT (landing): claims_raw   -- GRAIN: one row per claim
--   Intentionally PERMISSIVE. See design principle above. No PK on claim_id
--   (duplicates are a seeded DQ problem). Few NOT NULLs. Dates as TEXT so
--   impossible/missing dates load. Amounts NUMERIC so negatives load.
-- -----------------------------------------------------------------------------
CREATE TABLE claims_raw (
    -- identity / keys -----------------------------------------------------
    claim_id               TEXT,               -- NOT a PK here: dups are seeded on purpose
    patient_id             TEXT,               -- links claims to a patient (rebills, self-pay)

    -- segmentation keys (three different realistic join patterns) ---------
    payer_name_raw         TEXT,               -- MESSY free text -> standardized to dim_payer in cleaning
    service_line           TEXT,               -- clean-ish name -> dim_service_line.service_line_name
    provider_id            TEXT,               -- rendering provider (coding/denial patterns by provider)

    -- coding --------------------------------------------------------------
    cpt_code               TEXT,               -- procedure code (charge capture / coding signal)
    drg_code               TEXT,               -- DRG (inpatient grouping)

    -- the revenue cycle clock (TEXT ISO-8601 'YYYY-MM-DD') ----------------
    date_of_service        TEXT,               -- care delivered; start of the clock
    date_submitted         TEXT,               -- first claim submission (lag = throughput)
    date_paid              TEXT,               -- payment posted; NULL if open/unpaid (endpoint for days-in-AR)
    denial_date            TEXT,               -- when denied (NULL if not denied)

    -- dollars (NUMERIC; warehouse would use DECIMAL(12,2)) ----------------
    charge_amount          NUMERIC,            -- gross charge (inflated list price)
    allowed_amount         NUMERIC,            -- contractually allowed (managed care lives here)
    paid_amount            NUMERIC,            -- actually paid (net collection numerator)
    adjustment_amount      NUMERIC,            -- contractual write-offs + other adjustments
    patient_responsibility NUMERIC,            -- copay / coinsurance / deductible

    -- status & flags ------------------------------------------------------
    claim_status           TEXT,               -- Paid | Denied | Open | Partially Paid
    denial_flag            INTEGER,            -- 0/1 : denied at least once (denial-rate numerator)
    denial_reason_code     TEXT,               -- CARC code when denied -> dim_denial_reason (NULL otherwise)
    first_pass_flag        INTEGER,            -- 0/1 : adjudicated CLEAN on first submission (clean-claim numerator)
    rebill_flag            INTEGER             -- 0/1 : resubmission of a prior claim
);

-- -----------------------------------------------------------------------------
-- Indexes on the join/segmentation keys. Modest given the dataset size, but
-- they signal intent: these are the columns metrics group and join on.
-- -----------------------------------------------------------------------------
CREATE INDEX idx_claims_service_line ON claims_raw (service_line);
CREATE INDEX idx_claims_denial_code  ON claims_raw (denial_reason_code);
CREATE INDEX idx_claims_status       ON claims_raw (claim_status);

-- =============================================================================
-- End of schema. Data (including dimension reference rows) is loaded in
-- 01_load.sql -- DDL is kept separate from DML by convention.
-- =============================================================================
