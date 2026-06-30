-- =============================================================================
-- 99_segmentation.sql  -- REUSABLE segmentation layer: all 5 metrics, one grain
-- =============================================================================
-- v_segment_metrics computes every metric at payer_type x service_line in ONE
-- pass via conditional aggregation (each metric's CASE filters its own base).
--
-- DESIGN: store ADDITIVE COMPONENTS (counts + dollar sums), not just rates.
-- You cannot average percentages across segments -- rates must be recomputed
-- from numerator/denominator. With components stored, any coarser rollup =
-- SUM the components, THEN divide. One fine-grain view, correct at every grain.
--
-- This is the artifact a consultant reruns on a new client's extract: same SQL,
-- new data, full payer x service-line scorecard + any rollup.
-- Run:  sqlite3 revenue_cycle.db < sql/99_segmentation.sql
-- =============================================================================
.mode column
.headers on

DROP VIEW IF EXISTS v_segment_metrics;
CREATE VIEW v_segment_metrics AS
SELECT
    payer_type,
    service_line,
    -- ----- ADDITIVE COMPONENTS (sum these to roll up) -----------------------
    COUNT(*)                                                       AS n_claims,
    SUM(denial_flag)                                              AS n_denied,
    SUM(first_pass_flag)                                          AS n_clean,
    SUM(CASE WHEN claim_status IN ('Paid','Partially Paid') THEN paid_amount    ELSE 0 END) AS adj_paid,
    SUM(CASE WHEN claim_status IN ('Paid','Partially Paid') THEN allowed_amount ELSE 0 END) AS adj_allowed,
    SUM(CASE WHEN claim_status IN ('Paid','Partially Paid') THEN charge_amount  ELSE 0 END) AS adj_charge,
    SUM(CASE WHEN denial_flag = 1 THEN charge_amount ELSE 0 END)                            AS denied_charges,
    SUM(CASE WHEN claim_status = 'Open' THEN charge_amount ELSE 0 END)                      AS open_ar,
    SUM(CASE WHEN claim_status = 'Open' AND days_outstanding > 90 THEN charge_amount ELSE 0 END) AS open_ar_90plus,
    SUM(CASE WHEN claim_status IN ('Paid','Partially Paid') AND days_to_pay IS NOT NULL THEN 1 ELSE 0 END)            AS n_throughput,
    SUM(CASE WHEN claim_status IN ('Paid','Partially Paid') AND days_to_pay IS NOT NULL THEN days_to_pay ELSE 0 END)  AS sum_days_to_pay,
    -- ----- CONVENIENCE RATES (correct at THIS grain) ------------------------
    ROUND(100.0 * SUM(denial_flag)     / NULLIF(COUNT(*),0), 1)    AS denial_rate_pct,
    ROUND(100.0 * SUM(first_pass_flag) / NULLIF(COUNT(*),0), 1)    AS clean_claim_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN claim_status IN ('Paid','Partially Paid') THEN paid_amount    ELSE 0 END)
                / NULLIF(SUM(CASE WHEN claim_status IN ('Paid','Partially Paid') THEN allowed_amount ELSE 0 END),0), 1) AS net_collection_pct,
    ROUND(1.0 * SUM(CASE WHEN claim_status IN ('Paid','Partially Paid') AND days_to_pay IS NOT NULL THEN days_to_pay ELSE 0 END)
              / NULLIF(SUM(CASE WHEN claim_status IN ('Paid','Partially Paid') AND days_to_pay IS NOT NULL THEN 1 ELSE 0 END),0), 1) AS avg_days_to_pay
FROM v_claims_analytic
GROUP BY payer_type, service_line;

-- -----------------------------------------------------------------------------
-- A. The full payer x service-line scorecard (readable subset of columns).
-- -----------------------------------------------------------------------------
SELECT payer_type, service_line, n_claims,
       denial_rate_pct, clean_claim_rate_pct, net_collection_pct,
       avg_days_to_pay, open_ar_90plus
FROM v_segment_metrics
ORDER BY payer_type, service_line;

-- -----------------------------------------------------------------------------
-- B. ROLLUP to payer type -- by SUMMING components then dividing (NOT averaging
--    rates). Reconciles to denial_rate.sql / net_collection_rate.sql by payer.
-- -----------------------------------------------------------------------------
SELECT
    payer_type,
    SUM(n_claims)                                                  AS n_claims,
    ROUND(100.0 * SUM(n_denied) / NULLIF(SUM(n_claims),0), 1)      AS denial_rate_pct,
    ROUND(100.0 * SUM(n_clean)  / NULLIF(SUM(n_claims),0), 1)      AS clean_claim_rate_pct,
    ROUND(100.0 * SUM(adj_paid) / NULLIF(SUM(adj_allowed),0), 1)   AS net_collection_pct,
    ROUND(1.0 * SUM(sum_days_to_pay) / NULLIF(SUM(n_throughput),0), 1) AS avg_days_to_pay
FROM v_segment_metrics
GROUP BY payer_type
ORDER BY denial_rate_pct DESC;

-- -----------------------------------------------------------------------------
-- C. GRAND TOTAL -- same components, no GROUP BY. Reconciles to the overall
--    headline numbers (denial 12.2%, net 91.0%, clean 83.8%).
-- -----------------------------------------------------------------------------
SELECT
    SUM(n_claims)                                                  AS n_claims,
    ROUND(100.0 * SUM(n_denied) / NULLIF(SUM(n_claims),0), 1)      AS denial_rate_pct,
    ROUND(100.0 * SUM(n_clean)  / NULLIF(SUM(n_claims),0), 1)      AS clean_claim_rate_pct,
    ROUND(100.0 * SUM(adj_paid) / NULLIF(SUM(adj_allowed),0), 1)   AS net_collection_pct,
    ROUND(100.0 * SUM(adj_paid) / NULLIF(SUM(adj_charge),0), 1)    AS gross_collection_pct,
    ROUND(1.0 * SUM(sum_days_to_pay) / NULLIF(SUM(n_throughput),0), 1) AS avg_days_to_pay,
    ROUND(SUM(open_ar_90plus), 0)                                  AS open_ar_90plus_dollars
FROM v_segment_metrics;
