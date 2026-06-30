-- =============================================================================
-- 04_clean_views.sql  -- STAGE C: the TRUSTED LAYER (cleaning & standardization)
-- =============================================================================
-- This is the single source of truth. ALL metrics read from here; none re-clean.
-- Built as VIEWS (saved queries, computed on read, zero storage, cannot drift
-- from their definition). In a warehouse you might MATERIALIZE these as tables/
-- dbt models for speed; at this scale views are ideal.
--
-- Two layers:
--   v_claims_clean    -- every claim, standardized + DQ-flagged, nothing hidden
--   v_claims_analytic -- metric-ready subset: WHERE include_in_metrics = 1
--
-- Quarantine policy (NOT deletion):
--   HARD corruption (charge <= 0; date_paid < date_of_service) -> excluded
--       from the analytic layer but retained & flagged for audit.
--   SOFT missingness (missing pay date / denial reason) -> KEPT: still a valid
--       claim; only specific metrics are affected, handled per-metric. Dropping
--       a whole claim for one unused-by-most field would bias other metrics.
--
-- Run:  sqlite3 revenue_cycle.db < sql/04_clean_views.sql
-- =============================================================================

DROP VIEW IF EXISTS v_claims_analytic;
DROP VIEW IF EXISTS v_claims_clean;
DROP VIEW IF EXISTS v_params;

-- -----------------------------------------------------------------------------
-- v_params -- centralized parameters. The AR aging anchor lives in ONE place;
-- change it here and everything downstream follows. (A table would be the
-- editable alternative; a view is fine for a script-rebuilt DB.)
-- -----------------------------------------------------------------------------
CREATE VIEW v_params AS
SELECT '2025-01-15' AS as_of_date;          -- matches generator AS_OF_DATE

-- -----------------------------------------------------------------------------
-- v_claims_clean -- the standardized, de-duplicated, derived, flagged layer.
-- -----------------------------------------------------------------------------
CREATE VIEW v_claims_clean AS
WITH deduped AS (
    -- DEDUP via window function. ROW_NUMBER() OVER (PARTITION BY claim_id ...)
    -- numbers rows WITHIN each claim_id, restarting per id; ORDER BY rowid makes
    -- "which copy is #1" deterministic. Keeping rn = 1 drops exact duplicates.
    -- (Window functions keep every column, unlike GROUP BY which collapses.)
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY claim_id ORDER BY rowid) AS rn
    FROM claims_raw
),
mapped AS (
    -- PAYER STANDARDIZATION: normalize (UPPER+TRIM) then map by pattern to a
    -- canonical payer_id. Patterns generalize to unseen spellings; 'UNKNOWN'
    -- fallback makes any unmapped value visible instead of silently dropped.
    SELECT *,
        CASE
            WHEN UPPER(TRIM(payer_name_raw)) LIKE 'BCBS%'
              OR UPPER(TRIM(payer_name_raw)) LIKE '%BLUE CROSS%' THEN 'PAY001'
            WHEN UPPER(TRIM(payer_name_raw)) LIKE '%UNITED%'
              OR UPPER(TRIM(payer_name_raw)) = 'UHC'            THEN 'PAY002'
            WHEN UPPER(TRIM(payer_name_raw)) LIKE 'AETNA%'      THEN 'PAY003'
            WHEN UPPER(TRIM(payer_name_raw)) LIKE 'CIGNA%'      THEN 'PAY004'
            WHEN UPPER(TRIM(payer_name_raw)) LIKE '%MEDICARE%'  THEN 'PAY005'
            WHEN UPPER(TRIM(payer_name_raw)) LIKE '%MEDICAID%'  THEN 'PAY006'
            WHEN UPPER(TRIM(payer_name_raw)) LIKE '%SELF%'
              OR UPPER(TRIM(payer_name_raw)) = 'PATIENT'        THEN 'PAY007'
            ELSE 'UNKNOWN'
        END AS payer_id_std
    FROM deduped
    WHERE rn = 1                              -- <-- keep one row per claim_id
)
SELECT
    -- identity ----------------------------------------------------------------
    m.claim_id,
    m.patient_id,
    -- standardized payer (joined from canonical dimension) --------------------
    m.payer_id_std                       AS payer_id,
    p.payer_name,
    p.payer_type,
    -- service line + group ----------------------------------------------------
    m.service_line,
    sl.department_group,
    m.provider_id,
    m.cpt_code,
    m.drg_code,
    -- dates + month bucket ----------------------------------------------------
    m.date_of_service,
    m.date_submitted,
    m.date_paid,
    m.denial_date,
    substr(m.date_of_service, 1, 7)      AS service_month,    -- 'YYYY-MM'
    -- dollars -----------------------------------------------------------------
    m.charge_amount,
    m.allowed_amount,
    m.paid_amount,
    m.adjustment_amount,
    m.patient_responsibility,
    -- status / flags ----------------------------------------------------------
    m.claim_status,
    m.denial_flag,
    m.denial_reason_code,
    -- denied-but-missing-code -> 'Unknown' so reason mix still sums to 100% ----
    COALESCE(dr.reason_category,
             CASE WHEN m.denial_flag = 1 THEN 'Unknown' END) AS reason_category,
    m.first_pass_flag,
    m.rebill_flag,
    -- DERIVED TIMING (compute once here; metrics reuse) -----------------------
    -- julianday() is SQLite's serial-date fn; difference = days. Portability:
    -- Snowflake/SQL Server use DATEDIFF; Postgres uses date subtraction.
    CASE WHEN m.date_paid IS NOT NULL
         THEN CAST(julianday(m.date_paid) - julianday(m.date_of_service) AS INTEGER)
    END                                  AS days_to_pay,
    CASE WHEN m.claim_status = 'Open'
         THEN CAST(julianday((SELECT as_of_date FROM v_params))
                   - julianday(m.date_of_service) AS INTEGER)
    END                                  AS days_outstanding,
    -- DATA-QUALITY FLAGS ------------------------------------------------------
    CASE WHEN m.charge_amount <= 0 THEN 1 ELSE 0 END                AS flag_nonpositive_charge,
    CASE WHEN m.date_paid IS NOT NULL AND m.date_paid < m.date_of_service
         THEN 1 ELSE 0 END                                          AS flag_paid_before_service,
    CASE WHEN m.claim_status IN ('Paid','Partially Paid') AND m.date_paid IS NULL
         THEN 1 ELSE 0 END                                          AS flag_paid_missing_date,
    CASE WHEN m.denial_flag = 1 AND m.denial_reason_code IS NULL
         THEN 1 ELSE 0 END                                          AS flag_denied_missing_reason,
    -- metric gate: exclude HARD corruption only -------------------------------
    CASE WHEN m.charge_amount <= 0
           OR (m.date_paid IS NOT NULL AND m.date_paid < m.date_of_service)
         THEN 0 ELSE 1 END                                          AS include_in_metrics
FROM mapped m
LEFT JOIN dim_payer         p  ON m.payer_id_std      = p.payer_id
LEFT JOIN dim_service_line  sl ON m.service_line      = sl.service_line_name
LEFT JOIN dim_denial_reason dr ON m.denial_reason_code = dr.denial_reason_code;

-- -----------------------------------------------------------------------------
-- v_claims_analytic -- THE view metrics read. Metric-ready subset.
-- -----------------------------------------------------------------------------
CREATE VIEW v_claims_analytic AS
SELECT * FROM v_claims_clean
WHERE include_in_metrics = 1;

-- =============================================================================
-- VERIFICATION
-- =============================================================================
.mode column
.headers on

-- dedup worked? expect 5000 (was 5025)
SELECT COUNT(*) AS clean_rows, COUNT(DISTINCT claim_id) AS distinct_claims
FROM v_claims_clean;

-- standardization complete? expect 7 payers, ZERO 'UNKNOWN'
SELECT payer_id, payer_name, payer_type, COUNT(*) AS n_claims
FROM v_claims_clean
GROUP BY payer_id, payer_name, payer_type
ORDER BY n_claims DESC;

-- quarantine: how many rows gated out, and clean rows kept for metrics
SELECT
    SUM(CASE WHEN include_in_metrics = 0 THEN 1 ELSE 0 END) AS quarantined,
    SUM(include_in_metrics)                                  AS metric_ready,
    COUNT(*)                                                 AS total
FROM v_claims_clean;

-- soft flags retained (still in analytic layer): should still be present
SELECT
    SUM(flag_paid_missing_date)     AS paid_missing_date_kept,
    SUM(flag_denied_missing_reason) AS denied_missing_reason_kept
FROM v_claims_analytic;
