-- =============================================================================
-- metrics/denial_rate.sql  -- METRIC 1: Denial rate (count- and dollar-weighted)
-- =============================================================================
-- Definition (see METRIC_DEFINITIONS.md #1):
--   count  denial rate = denied claims / all claims
--   dollar denial rate = SUM(charge) of denied / SUM(charge) of all
--   Base: v_claims_analytic. INITIAL denial (denial_flag), partials not denied.
--   Dollar version uses CHARGE because denied claims have allowed = 0.
--
-- Reusability: the `flt` CTE holds parameters; the base filters with the
-- null-guard idiom (:param IS NULL OR col = :param) -> "unset = don't filter".
-- Rerun for any client/slice by editing ONLY the flt CTE.
-- Run:  sqlite3 revenue_cycle.db < sql/metrics/denial_rate.sql
-- =============================================================================
.mode column
.headers on

-- -----------------------------------------------------------------------------
-- Parameterized base. Set any of these to a value to scope the metric; leave
-- NULL for "all". (e.g. p_payer_type = 'Medicaid', p_month_start = '2024-07'.)
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_denial_base;
CREATE TEMP VIEW v_denial_base AS
WITH flt AS (
    SELECT
        NULL AS p_payer_type,      -- e.g. 'Commercial' | 'Medicare' | 'Medicaid' | 'Self-Pay'
        NULL AS p_service_line,     -- e.g. 'Cardiology'
        NULL AS p_month_start,      -- 'YYYY-MM' inclusive
        NULL AS p_month_end         -- 'YYYY-MM' inclusive
)
SELECT c.*
FROM v_claims_analytic c, flt
WHERE (flt.p_payer_type   IS NULL OR c.payer_type    = flt.p_payer_type)
  AND (flt.p_service_line  IS NULL OR c.service_line  = flt.p_service_line)
  AND (flt.p_month_start   IS NULL OR c.service_month >= flt.p_month_start)
  AND (flt.p_month_end     IS NULL OR c.service_month <= flt.p_month_end);

-- -----------------------------------------------------------------------------
-- Q1. OVERALL denial rate -- count- and dollar-weighted. Reconciles to ~12.2%.
--     SUM(denial_flag) sums a 0/1 column = count of denials (the rate pattern).
-- -----------------------------------------------------------------------------
SELECT
    COUNT(*)                                                       AS n_claims,
    SUM(denial_flag)                                              AS n_denied,
    ROUND(100.0 * SUM(denial_flag) / NULLIF(COUNT(*), 0), 1)       AS denial_rate_count_pct,
    ROUND(100.0 * SUM(CASE WHEN denial_flag = 1 THEN charge_amount ELSE 0 END)
                / NULLIF(SUM(charge_amount), 0), 1)                AS denial_rate_dollar_pct
FROM v_denial_base;

-- -----------------------------------------------------------------------------
-- Q2. By PAYER TYPE -- should mirror the generating process
--     (Medicaid highest, Medicare lowest).
-- -----------------------------------------------------------------------------
SELECT
    payer_type,
    COUNT(*)                                                       AS n_claims,
    SUM(denial_flag)                                              AS n_denied,
    ROUND(100.0 * SUM(denial_flag) / NULLIF(COUNT(*), 0), 1)       AS denial_rate_count_pct,
    ROUND(100.0 * SUM(CASE WHEN denial_flag = 1 THEN charge_amount ELSE 0 END)
                / NULLIF(SUM(charge_amount), 0), 1)                AS denial_rate_dollar_pct
FROM v_denial_base
GROUP BY payer_type
ORDER BY denial_rate_count_pct DESC;

-- -----------------------------------------------------------------------------
-- Q3. By SERVICE LINE -- where do denials concentrate clinically.
-- -----------------------------------------------------------------------------
SELECT
    service_line,
    COUNT(*)                                                       AS n_claims,
    SUM(denial_flag)                                              AS n_denied,
    ROUND(100.0 * SUM(denial_flag) / NULLIF(COUNT(*), 0), 1)       AS denial_rate_count_pct
FROM v_denial_base
GROUP BY service_line
ORDER BY denial_rate_count_pct DESC;
