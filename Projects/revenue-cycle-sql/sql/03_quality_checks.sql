-- =============================================================================
-- 03_quality_checks.sql  -- STAGE B: missingness & data-quality checks (read-only)
-- =============================================================================
-- Purpose: measure missingness and run logical-consistency checks. We do NOT
-- fix anything here -- this stage produces a documented list of defects and
-- their counts, reconciled against the generator's ground truth. Cleaning
-- happens next, in 04_clean_views.sql.
-- Run:  sqlite3 revenue_cycle.db < sql/03_quality_checks.sql
-- =============================================================================
.mode column
.headers on

-- -----------------------------------------------------------------------------
-- B1. MISSINGNESS PROFILE -- null count + null % per column of interest.
--     Interpretation (done in prose, not SQL): some nulls are STRUCTURAL and
--     correct (denial_date null on non-denied claims; date_paid null on Open
--     claims), others are PROBLEMATIC (date_paid null on a Paid claim). The
--     number alone is neutral; meaning comes from reading it against status.
-- -----------------------------------------------------------------------------
SELECT 'date_paid' AS column_name,
       SUM(CASE WHEN date_paid IS NULL THEN 1 ELSE 0 END)                AS n_null,
       ROUND(100.0 * SUM(CASE WHEN date_paid IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_null
FROM claims_raw
UNION ALL
SELECT 'denial_date',
       SUM(CASE WHEN denial_date IS NULL THEN 1 ELSE 0 END),
       ROUND(100.0 * SUM(CASE WHEN denial_date IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1)
FROM claims_raw
UNION ALL
SELECT 'denial_reason_code',
       SUM(CASE WHEN denial_reason_code IS NULL THEN 1 ELSE 0 END),
       ROUND(100.0 * SUM(CASE WHEN denial_reason_code IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1)
FROM claims_raw
UNION ALL
SELECT 'drg_code',
       SUM(CASE WHEN drg_code IS NULL THEN 1 ELSE 0 END),
       ROUND(100.0 * SUM(CASE WHEN drg_code IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1)
FROM claims_raw
UNION ALL
SELECT 'payer_name_raw',
       SUM(CASE WHEN payer_name_raw IS NULL OR TRIM(payer_name_raw) = '' THEN 1 ELSE 0 END),
       ROUND(100.0 * SUM(CASE WHEN payer_name_raw IS NULL OR TRIM(payer_name_raw) = '' THEN 1 ELSE 0 END) / COUNT(*), 1)
FROM claims_raw
UNION ALL
SELECT 'service_line',
       SUM(CASE WHEN service_line IS NULL OR TRIM(service_line) = '' THEN 1 ELSE 0 END),
       ROUND(100.0 * SUM(CASE WHEN service_line IS NULL OR TRIM(service_line) = '' THEN 1 ELSE 0 END) / COUNT(*), 1)
FROM claims_raw;

-- -----------------------------------------------------------------------------
-- B2. DATA-QUALITY SCORECARD -- the SEEDED defects, with expected counts.
--     Each row: check name, how many rows we flagged, and the ground-truth
--     value from the generator. n_flagged should equal expected = the check
--     is proven correct, not just plausible.
--
--     New idea below: HAVING. WHERE filters individual rows BEFORE grouping;
--     HAVING filters GROUPS AFTER aggregation. Duplicate detection needs
--     HAVING because "appears more than once" is a property of a GROUP.
-- -----------------------------------------------------------------------------
SELECT 'duplicate_claim_ids' AS check_name,
       (SELECT COUNT(*) FROM (
            SELECT claim_id FROM claims_raw
            GROUP BY claim_id HAVING COUNT(*) > 1)) AS n_flagged,
       25 AS expected
UNION ALL
SELECT 'paid_missing_paydate',
       SUM(CASE WHEN claim_status IN ('Paid','Partially Paid') AND date_paid IS NULL THEN 1 ELSE 0 END),
       116
FROM claims_raw
UNION ALL
SELECT 'denied_missing_reason',
       SUM(CASE WHEN denial_flag = 1 AND denial_reason_code IS NULL THEN 1 ELSE 0 END),
       30
FROM claims_raw
UNION ALL
SELECT 'paid_before_service',
       SUM(CASE WHEN date_paid IS NOT NULL AND date_paid < date_of_service THEN 1 ELSE 0 END),
       15
FROM claims_raw
UNION ALL
SELECT 'nonpositive_charge',
       SUM(CASE WHEN charge_amount <= 0 THEN 1 ELSE 0 END),
       10
FROM claims_raw;

-- -----------------------------------------------------------------------------
-- B3. DUPLICATE DETAIL -- show a few offending claim_ids (the HAVING pattern
--     used directly). These are the ids that appear more than once.
-- -----------------------------------------------------------------------------
SELECT claim_id, COUNT(*) AS n_rows
FROM claims_raw
GROUP BY claim_id
HAVING COUNT(*) > 1
ORDER BY claim_id
LIMIT 5;

-- -----------------------------------------------------------------------------
-- B4. ADDITIONAL INTEGRITY CHECKS -- NOT seeded. The battery an analyst runs
--     anyway. A 0 is a valid, valuable result (the rule holds). A non-zero is
--     a finding to investigate. No "expected" column -- these are exploratory.
-- -----------------------------------------------------------------------------
SELECT 'flag_status_mismatch' AS check_name,
       SUM(CASE WHEN (denial_flag = 1 AND claim_status <> 'Denied')
                  OR (denial_flag = 0 AND claim_status =  'Denied')
                THEN 1 ELSE 0 END) AS n_flagged
FROM claims_raw
UNION ALL
SELECT 'submitted_before_service',
       SUM(CASE WHEN date_submitted < date_of_service THEN 1 ELSE 0 END)
FROM claims_raw
UNION ALL
SELECT 'allowed_exceeds_charge',
       SUM(CASE WHEN allowed_amount > charge_amount THEN 1 ELSE 0 END)
FROM claims_raw
UNION ALL
SELECT 'paid_exceeds_allowed',
       SUM(CASE WHEN paid_amount > allowed_amount THEN 1 ELSE 0 END)
FROM claims_raw;
