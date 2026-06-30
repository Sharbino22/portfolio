-- =============================================================================
-- metrics/net_collection_rate.sql  -- METRIC 4: Net collection rate (+ gross)
-- =============================================================================
-- Definition (see METRIC_DEFINITIONS.md #4):
--   NET collection   = SUM(paid_amount) / SUM(allowed_amount)
--   GROSS collection = SUM(paid_amount) / SUM(charge_amount)   [contrast only]
--   Base: adjudicated claims (Paid / Partially Paid) with allowed > 0.
--     - Denied excluded (allowed = 0; the >0 guard drops them).
--     - Open EXCLUDED: they have allowed>0 but paid=0 only because not yet paid,
--       not underpaid -- including them would falsely depress net collection.
--
-- The point: charges are inflated list prices, so gross looks low (~45%) while
-- net is healthy (~91%). The gap = contractual adjustment, NOT a collection
-- failure. Net measures collection PERFORMANCE; gross is contaminated by each
-- payer's CONTRACT rate. NULLIF guards divide-by-zero.
-- Run:  sqlite3 revenue_cycle.db < sql/metrics/net_collection_rate.sql
-- =============================================================================
.mode column
.headers on

-- adjudicated base (parameterized null-guard pattern)
DROP VIEW IF EXISTS v_collect_base;
CREATE TEMP VIEW v_collect_base AS
WITH flt AS (
    SELECT NULL AS p_payer_type, NULL AS p_service_line,
           NULL AS p_month_start, NULL AS p_month_end
)
SELECT c.*
FROM v_claims_analytic c, flt
WHERE c.claim_status IN ('Paid','Partially Paid')
  AND c.allowed_amount > 0
  AND (flt.p_payer_type  IS NULL OR c.payer_type    = flt.p_payer_type)
  AND (flt.p_service_line IS NULL OR c.service_line  = flt.p_service_line)
  AND (flt.p_month_start  IS NULL OR c.service_month >= flt.p_month_start)
  AND (flt.p_month_end    IS NULL OR c.service_month <= flt.p_month_end);

-- -----------------------------------------------------------------------------
-- Q1. OVERALL net vs gross -- the headline contrast.
-- -----------------------------------------------------------------------------
SELECT
    COUNT(*)                                                       AS n_claims,
    ROUND(SUM(charge_amount), 0)                                   AS total_charges,
    ROUND(SUM(allowed_amount), 0)                                  AS total_allowed,
    ROUND(SUM(paid_amount), 0)                                     AS total_paid,
    ROUND(100.0 * SUM(paid_amount) / NULLIF(SUM(allowed_amount),0), 1) AS net_collection_pct,
    ROUND(100.0 * SUM(paid_amount) / NULLIF(SUM(charge_amount),0), 1)  AS gross_collection_pct
FROM v_collect_base;

-- -----------------------------------------------------------------------------
-- Q2. By PAYER TYPE -- net should be ~stable (performance); gross varies wildly
--     (contract rate). contract_ratio = allowed/charge exposes managed-care terms.
-- -----------------------------------------------------------------------------
SELECT
    payer_type,
    COUNT(*)                                                       AS n_claims,
    ROUND(100.0 * SUM(allowed_amount) / NULLIF(SUM(charge_amount),0), 1)  AS contract_ratio_pct,
    ROUND(100.0 * SUM(paid_amount) / NULLIF(SUM(allowed_amount),0), 1)    AS net_collection_pct,
    ROUND(100.0 * SUM(paid_amount) / NULLIF(SUM(charge_amount),0), 1)     AS gross_collection_pct
FROM v_collect_base
GROUP BY payer_type
ORDER BY net_collection_pct DESC;

-- -----------------------------------------------------------------------------
-- Q3. By SERVICE LINE -- net collection.
-- -----------------------------------------------------------------------------
SELECT
    service_line,
    COUNT(*)                                                       AS n_claims,
    ROUND(100.0 * SUM(paid_amount) / NULLIF(SUM(allowed_amount),0), 1) AS net_collection_pct
FROM v_collect_base
GROUP BY service_line
ORDER BY net_collection_pct DESC;
