-- =============================================================================
-- metrics/clean_claim_rate.sql  -- METRIC 5: Clean claim rate (+ link to denials)
-- =============================================================================
-- Definition (see METRIC_DEFINITIONS.md #5):
--   clean claim rate = claims with first_pass_flag = 1 / all submitted claims.
--   Base: v_claims_analytic (all metric-ready claims are submitted).
--   "Clean" = adjudicated cleanly on FIRST submission, no edits/rework -- STRICTER
--   than "not denied". A claim can be paid yet not clean (needed a resubmission).
--
-- Q4 closes the cross-metric narrative: clean claim rate is a LEADING INDICATOR
-- of denials. We show denial rate among clean vs non-clean claims to prove it.
-- Run:  sqlite3 revenue_cycle.db < sql/metrics/clean_claim_rate.sql
-- =============================================================================
.mode column
.headers on

-- submitted base (parameterized null-guard pattern)
DROP VIEW IF EXISTS v_clean_base;
CREATE TEMP VIEW v_clean_base AS
WITH flt AS (
    SELECT NULL AS p_payer_type, NULL AS p_service_line,
           NULL AS p_month_start, NULL AS p_month_end
)
SELECT c.*
FROM v_claims_analytic c, flt
WHERE (flt.p_payer_type  IS NULL OR c.payer_type    = flt.p_payer_type)
  AND (flt.p_service_line IS NULL OR c.service_line  = flt.p_service_line)
  AND (flt.p_month_start  IS NULL OR c.service_month >= flt.p_month_start)
  AND (flt.p_month_end    IS NULL OR c.service_month <= flt.p_month_end);

-- -----------------------------------------------------------------------------
-- Q1. OVERALL clean claim rate.
-- -----------------------------------------------------------------------------
SELECT
    COUNT(*)                                                       AS n_submitted,
    SUM(first_pass_flag)                                          AS n_clean,
    ROUND(100.0 * SUM(first_pass_flag) / NULLIF(COUNT(*),0), 1)    AS clean_claim_rate_pct
FROM v_clean_base;

-- -----------------------------------------------------------------------------
-- Q2. By PAYER TYPE.
-- -----------------------------------------------------------------------------
SELECT
    payer_type,
    COUNT(*)                                                       AS n_submitted,
    ROUND(100.0 * SUM(first_pass_flag) / NULLIF(COUNT(*),0), 1)    AS clean_claim_rate_pct
FROM v_clean_base
GROUP BY payer_type
ORDER BY clean_claim_rate_pct DESC;

-- -----------------------------------------------------------------------------
-- Q3. By SERVICE LINE.
-- -----------------------------------------------------------------------------
SELECT
    service_line,
    COUNT(*)                                                       AS n_submitted,
    ROUND(100.0 * SUM(first_pass_flag) / NULLIF(COUNT(*),0), 1)    AS clean_claim_rate_pct
FROM v_clean_base
GROUP BY service_line
ORDER BY clean_claim_rate_pct DESC;

-- -----------------------------------------------------------------------------
-- Q4. THE NARRATIVE LINK -- denial rate among CLEAN vs NON-CLEAN claims.
--     If clean claims deny far less than non-clean, clean claim rate is a
--     leading indicator of denials (front-end discipline -> fewer denials).
-- -----------------------------------------------------------------------------
SELECT
    CASE WHEN first_pass_flag = 1 THEN 'Clean (first-pass)'
         ELSE 'Not clean (reworked)' END                          AS claim_path,
    COUNT(*)                                                       AS n_claims,
    SUM(denial_flag)                                              AS n_denied,
    ROUND(100.0 * SUM(denial_flag) / NULLIF(COUNT(*),0), 1)        AS denial_rate_pct
FROM v_clean_base
GROUP BY first_pass_flag
ORDER BY first_pass_flag DESC;
