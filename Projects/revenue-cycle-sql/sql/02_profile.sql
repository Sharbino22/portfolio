-- =============================================================================
-- 02_profile.sql  -- STAGE A: exploration & profiling (read-only)
-- =============================================================================
-- Purpose: "get to know the file" before defining any metric. No changes to
-- data. We profile categoricals, numeric ranges, dates, and key cardinality.
-- Run:  sqlite3 revenue_cycle.db < sql/02_profile.sql
-- =============================================================================
.mode column
.headers on

-- -----------------------------------------------------------------------------
-- A1. Claim status distribution (count + share of total).
--     SUM(...)*100.0/(SELECT COUNT(*)...) is "conditional aggregation" for a %.
-- -----------------------------------------------------------------------------
SELECT
    claim_status,
    COUNT(*)                                              AS n_claims,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims_raw), 1) AS pct
FROM claims_raw
GROUP BY claim_status
ORDER BY n_claims DESC;

-- -----------------------------------------------------------------------------
-- A2. Raw payer-name spellings -- exposes the dirt that cleaning must fix.
--     One canonical payer is hiding behind many spellings here.
-- -----------------------------------------------------------------------------
SELECT
    payer_name_raw,
    COUNT(*) AS n_claims
FROM claims_raw
GROUP BY payer_name_raw
ORDER BY n_claims DESC;

-- -----------------------------------------------------------------------------
-- A3. Service-line distribution (count + share).
-- -----------------------------------------------------------------------------
SELECT
    service_line,
    COUNT(*)                                              AS n_claims,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims_raw), 1) AS pct
FROM claims_raw
GROUP BY service_line
ORDER BY n_claims DESC;

-- -----------------------------------------------------------------------------
-- A4. Denial-reason distribution, joined to the dimension for the category.
--     LEFT JOIN so denied claims with a MISSING reason code still appear
--     (they fall under a NULL category -- a thing we want to see, not hide).
--     WHERE denial_flag = 1 restricts to denied claims only.
-- -----------------------------------------------------------------------------
SELECT
    c.denial_reason_code,
    d.reason_category,
    COUNT(*) AS n_denied
FROM claims_raw AS c
LEFT JOIN dim_denial_reason AS d
       ON c.denial_reason_code = d.denial_reason_code
WHERE c.denial_flag = 1
GROUP BY c.denial_reason_code, d.reason_category
ORDER BY n_denied DESC;

-- -----------------------------------------------------------------------------
-- A5. Numeric profiling of the money columns, one row per column via UNION ALL.
--     For each: row count, #NULL, #non-positive (<=0), min, max, average.
--     This is how you spot impossible values (negatives) and structural zeros
--     (denied/open claims have allowed=0, paid=0).
-- -----------------------------------------------------------------------------
SELECT 'charge_amount' AS metric,
       COUNT(*)                                                  AS n_rows,
       SUM(CASE WHEN charge_amount IS NULL THEN 1 ELSE 0 END)    AS n_null,
       SUM(CASE WHEN charge_amount <= 0   THEN 1 ELSE 0 END)     AS n_nonpos,
       MIN(charge_amount) AS min_val, MAX(charge_amount) AS max_val,
       ROUND(AVG(charge_amount), 2) AS avg_val
FROM claims_raw
UNION ALL
SELECT 'allowed_amount', COUNT(*),
       SUM(CASE WHEN allowed_amount IS NULL THEN 1 ELSE 0 END),
       SUM(CASE WHEN allowed_amount <= 0   THEN 1 ELSE 0 END),
       MIN(allowed_amount), MAX(allowed_amount), ROUND(AVG(allowed_amount), 2)
FROM claims_raw
UNION ALL
SELECT 'paid_amount', COUNT(*),
       SUM(CASE WHEN paid_amount IS NULL THEN 1 ELSE 0 END),
       SUM(CASE WHEN paid_amount <= 0   THEN 1 ELSE 0 END),
       MIN(paid_amount), MAX(paid_amount), ROUND(AVG(paid_amount), 2)
FROM claims_raw
UNION ALL
SELECT 'adjustment_amount', COUNT(*),
       SUM(CASE WHEN adjustment_amount IS NULL THEN 1 ELSE 0 END),
       SUM(CASE WHEN adjustment_amount <= 0   THEN 1 ELSE 0 END),
       MIN(adjustment_amount), MAX(adjustment_amount), ROUND(AVG(adjustment_amount), 2)
FROM claims_raw
UNION ALL
SELECT 'patient_responsibility', COUNT(*),
       SUM(CASE WHEN patient_responsibility IS NULL THEN 1 ELSE 0 END),
       SUM(CASE WHEN patient_responsibility <= 0   THEN 1 ELSE 0 END),
       MIN(patient_responsibility), MAX(patient_responsibility),
       ROUND(AVG(patient_responsibility), 2)
FROM claims_raw;

-- -----------------------------------------------------------------------------
-- A6. Date spans + null counts for each date column.
--     Dates are ISO TEXT, so MIN/MAX sort correctly as strings.
-- -----------------------------------------------------------------------------
SELECT 'date_of_service' AS date_col,
       MIN(date_of_service) AS min_date, MAX(date_of_service) AS max_date,
       SUM(CASE WHEN date_of_service IS NULL THEN 1 ELSE 0 END) AS n_null
FROM claims_raw
UNION ALL
SELECT 'date_submitted', MIN(date_submitted), MAX(date_submitted),
       SUM(CASE WHEN date_submitted IS NULL THEN 1 ELSE 0 END) FROM claims_raw
UNION ALL
SELECT 'date_paid', MIN(date_paid), MAX(date_paid),
       SUM(CASE WHEN date_paid IS NULL THEN 1 ELSE 0 END) FROM claims_raw
UNION ALL
SELECT 'denial_date', MIN(denial_date), MAX(denial_date),
       SUM(CASE WHEN denial_date IS NULL THEN 1 ELSE 0 END) FROM claims_raw;

-- -----------------------------------------------------------------------------
-- A7. Key cardinality -- how many DISTINCT values in the identifier columns.
--     Reveals grain (claim_id near-unique) and fan-out (patients repeat).
-- -----------------------------------------------------------------------------
SELECT
    COUNT(*)                        AS total_rows,
    COUNT(DISTINCT claim_id)        AS distinct_claims,
    COUNT(DISTINCT patient_id)      AS distinct_patients,
    COUNT(DISTINCT provider_id)     AS distinct_providers,
    COUNT(DISTINCT cpt_code)        AS distinct_cpt
FROM claims_raw;
