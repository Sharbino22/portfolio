-- =============================================================================
-- metrics/denial_reason_mix.sql  -- METRIC 2: Denial reason mix
-- =============================================================================
-- Definition (see METRIC_DEFINITIONS.md #2):
--   Base = denied claims only (denial_flag = 1) in v_claims_analytic.
--   Per reason_category: share of denied COUNT and denied CHARGES.
--   'Unknown' bucket holds denied-but-missing-code claims (mix still = 100%).
--   "Preventable (front-end)" = Authorization + Eligibility + Coding.
--
-- New idea: share-of-total via window function. After GROUP BY, COUNT(*) is the
-- per-group count; SUM(COUNT(*)) OVER () sums those across ALL groups = grand
-- total -- a percentage denominator with no extra table scan. OVER () = "whole
-- result set is the window".
--
-- Reusable: same flt-CTE null-guard parameterization as denial_rate.sql.
-- Run:  sqlite3 revenue_cycle.db < sql/metrics/denial_reason_mix.sql
-- =============================================================================
.mode column
.headers on

-- denied-claims base, parameterized + restricted to denial_flag = 1
DROP VIEW IF EXISTS v_denied_base;
CREATE TEMP VIEW v_denied_base AS
WITH flt AS (
    SELECT NULL AS p_payer_type, NULL AS p_service_line,
           NULL AS p_month_start, NULL AS p_month_end
)
SELECT c.*
FROM v_claims_analytic c, flt
WHERE c.denial_flag = 1
  AND (flt.p_payer_type  IS NULL OR c.payer_type    = flt.p_payer_type)
  AND (flt.p_service_line IS NULL OR c.service_line  = flt.p_service_line)
  AND (flt.p_month_start  IS NULL OR c.service_month >= flt.p_month_start)
  AND (flt.p_month_end    IS NULL OR c.service_month <= flt.p_month_end);

-- -----------------------------------------------------------------------------
-- Q1. Reason mix by CATEGORY -- count share and dollar share side by side.
--     SUM(COUNT(*)) OVER ()       = total denied claims (count denominator)
--     SUM(SUM(charge)) OVER ()    = total denied charges (dollar denominator)
-- -----------------------------------------------------------------------------
SELECT
    reason_category,
    COUNT(*)                                                       AS n_denied,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)             AS pct_of_denied_count,
    ROUND(SUM(charge_amount), 0)                                   AS denied_charges,
    ROUND(100.0 * SUM(charge_amount) / SUM(SUM(charge_amount)) OVER (), 1)
                                                                   AS pct_of_denied_dollars
FROM v_denied_base
GROUP BY reason_category
ORDER BY n_denied DESC;

-- -----------------------------------------------------------------------------
-- Q2. Granular: individual reason CODE + description (rank by frequency).
-- -----------------------------------------------------------------------------
SELECT
    COALESCE(denial_reason_code, '(missing)')  AS denial_reason_code,
    COALESCE(reason_category, 'Unknown')       AS reason_category,
    COUNT(*)                                   AS n_denied,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_denied
FROM v_denied_base
GROUP BY denial_reason_code, reason_category
ORDER BY n_denied DESC;

-- -----------------------------------------------------------------------------
-- Q3. PREVENTABLE rollup -- the headline story. Map categories to actionability.
-- -----------------------------------------------------------------------------
SELECT
    CASE
        WHEN reason_category IN ('Authorization','Eligibility','Coding')
            THEN 'Preventable (front-end)'
        WHEN reason_category = 'Unknown'
            THEN 'Unknown (missing code)'
        ELSE 'Payer-driven / Other'
    END                                                            AS actionability,
    COUNT(*)                                                       AS n_denied,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)             AS pct_of_denied_count,
    ROUND(100.0 * SUM(charge_amount) / SUM(SUM(charge_amount)) OVER (), 1)
                                                                   AS pct_of_denied_dollars
FROM v_denied_base
GROUP BY actionability
ORDER BY n_denied DESC;
