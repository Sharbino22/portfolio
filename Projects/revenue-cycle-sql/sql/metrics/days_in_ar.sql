-- =============================================================================
-- metrics/days_in_ar.sql  -- METRIC 3: Days in AR (throughput) + aging buckets
-- =============================================================================
-- Definition (see METRIC_DEFINITIONS.md #3):
--   3a Throughput: days_to_pay = date_paid - date_of_service, for Paid/Partially
--      Paid with a pay date. Report MEDIAN and MEAN (AR is right-skewed).
--   3b Open AR aging: for Open claims, days_outstanding = as_of - date_of_service,
--      bucketed 0-30/31-60/61-90/90+; report count and outstanding $ (= charge).
--   Clock starts at date_of_service. as_of_date from v_params.
--
-- SQLite has no MEDIAN/PERCENTILE_CONT (Snowflake/Postgres do). We build median
-- by ranking with a window function and picking the middle row(s):
--     rn IN ((cnt+1)/2, (cnt+2)/2)  -- odd: one middle row; even: two, averaged.
-- Run:  sqlite3 revenue_cycle.db < sql/metrics/days_in_ar.sql
-- =============================================================================
.mode column
.headers on

-- =============================================================================
-- PART A -- PAID THROUGHPUT (days to pay)
-- =============================================================================

-- A1. Overall: n, mean, median, min, max.
WITH paid AS (
    SELECT days_to_pay
    FROM v_claims_analytic
    WHERE claim_status IN ('Paid','Partially Paid') AND days_to_pay IS NOT NULL
),
ranked AS (
    SELECT days_to_pay,
           ROW_NUMBER() OVER (ORDER BY days_to_pay) AS rn,
           COUNT(*)     OVER ()                     AS cnt
    FROM paid
)
SELECT
    (SELECT COUNT(*)            FROM paid)                          AS n_paid,
    (SELECT ROUND(AVG(days_to_pay),1) FROM paid)                   AS mean_days,
    (SELECT ROUND(AVG(days_to_pay),1) FROM ranked
       WHERE rn IN ((cnt+1)/2, (cnt+2)/2))                         AS median_days,
    (SELECT MIN(days_to_pay)    FROM paid)                          AS min_days,
    (SELECT MAX(days_to_pay)    FROM paid)                          AS max_days;

-- A2. Throughput by PAYER TYPE -- mean + median (median via partitioned window).
WITH paid AS (
    SELECT payer_type, days_to_pay
    FROM v_claims_analytic
    WHERE claim_status IN ('Paid','Partially Paid') AND days_to_pay IS NOT NULL
),
stats AS (
    SELECT payer_type, COUNT(*) AS n_paid, ROUND(AVG(days_to_pay),1) AS mean_days
    FROM paid GROUP BY payer_type
),
ranked AS (
    SELECT payer_type, days_to_pay,
           ROW_NUMBER() OVER (PARTITION BY payer_type ORDER BY days_to_pay) AS rn,
           COUNT(*)     OVER (PARTITION BY payer_type)                       AS cnt
    FROM paid
),
med AS (
    SELECT payer_type, ROUND(AVG(days_to_pay),1) AS median_days
    FROM ranked WHERE rn IN ((cnt+1)/2, (cnt+2)/2)
    GROUP BY payer_type
)
SELECT s.payer_type, s.n_paid, s.mean_days, m.median_days
FROM stats s JOIN med m USING (payer_type)
ORDER BY s.mean_days DESC;

-- =============================================================================
-- PART B -- OPEN AR AGING
-- =============================================================================

-- B1. Aging buckets overall -- count, outstanding $, and share of open $.
WITH open_ar AS (
    SELECT charge_amount,
           CASE WHEN days_outstanding <= 30 THEN '0-30'
                WHEN days_outstanding <= 60 THEN '31-60'
                WHEN days_outstanding <= 90 THEN '61-90'
                ELSE '90+' END AS bucket,
           CASE WHEN days_outstanding <= 30 THEN 1
                WHEN days_outstanding <= 60 THEN 2
                WHEN days_outstanding <= 90 THEN 3
                ELSE 4 END AS bucket_sort
    FROM v_claims_analytic
    WHERE claim_status = 'Open'
)
SELECT
    bucket,
    COUNT(*)                                                       AS n_open_claims,
    ROUND(SUM(charge_amount), 0)                                   AS outstanding_dollars,
    ROUND(100.0 * SUM(charge_amount) / SUM(SUM(charge_amount)) OVER (), 1)
                                                                   AS pct_of_open_dollars
FROM open_ar
GROUP BY bucket, bucket_sort
ORDER BY bucket_sort;

-- B2. Aging PIVOT by payer type -- outstanding $ per bucket, one row per payer.
--     Conditional aggregation turns bucket VALUES into COLUMNS (the Excel shape).
WITH open_ar AS (
    SELECT payer_type, charge_amount,
           CASE WHEN days_outstanding <= 30 THEN '0-30'
                WHEN days_outstanding <= 60 THEN '31-60'
                WHEN days_outstanding <= 90 THEN '61-90'
                ELSE '90+' END AS bucket
    FROM v_claims_analytic
    WHERE claim_status = 'Open'
)
SELECT
    payer_type,
    ROUND(SUM(CASE WHEN bucket = '0-30'  THEN charge_amount ELSE 0 END), 0) AS d_0_30,
    ROUND(SUM(CASE WHEN bucket = '31-60' THEN charge_amount ELSE 0 END), 0) AS d_31_60,
    ROUND(SUM(CASE WHEN bucket = '61-90' THEN charge_amount ELSE 0 END), 0) AS d_61_90,
    ROUND(SUM(CASE WHEN bucket = '90+'   THEN charge_amount ELSE 0 END), 0) AS d_90_plus,
    ROUND(SUM(charge_amount), 0)                                            AS total_open
FROM open_ar
GROUP BY payer_type
ORDER BY total_open DESC;
