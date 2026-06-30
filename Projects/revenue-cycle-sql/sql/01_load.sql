-- =============================================================================
-- 01_load.sql  -- load raw CSVs into the schema, normalize empty -> NULL, verify
-- =============================================================================
-- Run AFTER 00_schema.sql, from the PROJECT ROOT so the relative CSV paths
-- resolve:
--     sqlite3 revenue_cycle.db < sql/00_schema.sql
--     sqlite3 revenue_cycle.db < sql/01_load.sql
--
-- Loading is inherently engine-specific. Here we use SQLite's .import dot-command.
-- Warehouse equivalents:  Snowflake -> COPY INTO ;  SQL Server -> BULK INSERT/BCP ;
-- Postgres -> COPY.  The ANALYTICAL SQL (everything downstream) stays portable;
-- only this load file is SQLite-flavored.
-- =============================================================================

-- .import maps CSV columns BY POSITION into the existing table, so CSV column
-- order must match the table definition (it does -- the generator writes in
-- schema order). --skip 1 drops the header row (the table already exists, so
-- SQLite will not treat row 1 as a header on its own).

.mode csv

.import --skip 1 data/raw/dim_payer.csv         dim_payer
.import --skip 1 data/raw/dim_service_line.csv  dim_service_line
.import --skip 1 data/raw/dim_denial_reason.csv dim_denial_reason
.import --skip 1 data/raw/claims_raw.csv        claims_raw

-- -----------------------------------------------------------------------------
-- TECHNICAL normalization only: CSV cannot encode NULL, so missing values
-- arrive as empty strings ''. Convert the genuinely-nullable columns to real
-- NULLs so Stage B measures true missingness and logical checks work.
-- This is encoding-level, NOT semantic cleaning -- payer-name standardization,
-- dedup, etc. all wait for the trusted layer in 04_clean_views.sql.
-- -----------------------------------------------------------------------------
UPDATE claims_raw SET date_paid          = NULL WHERE date_paid          = '';
UPDATE claims_raw SET denial_date        = NULL WHERE denial_date        = '';
UPDATE claims_raw SET denial_reason_code = NULL WHERE denial_reason_code = '';
UPDATE claims_raw SET drg_code           = NULL WHERE drg_code           = '';

-- -----------------------------------------------------------------------------
-- VERIFICATION -- reconcile against the generator's ground truth.
-- -----------------------------------------------------------------------------
.mode column
.headers on

SELECT 'dim_payer'         AS table_name, COUNT(*) AS rows FROM dim_payer
UNION ALL SELECT 'dim_service_line',  COUNT(*) FROM dim_service_line
UNION ALL SELECT 'dim_denial_reason', COUNT(*) FROM dim_denial_reason
UNION ALL SELECT 'claims_raw',        COUNT(*) FROM claims_raw;

-- duplicate landing check: total rows vs distinct claim_id (expect 5025 vs 5000)
SELECT COUNT(*)                  AS total_rows,
       COUNT(DISTINCT claim_id)  AS distinct_claims,
       COUNT(*) - COUNT(DISTINCT claim_id) AS duplicate_rows
FROM claims_raw;

-- spot-check that seeded dirt survived the load (should echo ground truth)
SELECT
    SUM(CASE WHEN denial_flag = 1 AND denial_reason_code IS NULL THEN 1 ELSE 0 END)
        AS denied_missing_reason,         -- expect ~30
    SUM(CASE WHEN claim_status IN ('Paid','Partially Paid') AND date_paid IS NULL THEN 1 ELSE 0 END)
        AS paid_missing_paydate,          -- expect ~116
    SUM(CASE WHEN charge_amount <= 0 THEN 1 ELSE 0 END)
        AS nonpositive_charge             -- expect ~10
FROM claims_raw;
