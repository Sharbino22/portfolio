"""
generate_data.py -- synthetic revenue cycle claims generator.

Produces four CSVs in data/raw/:
    dim_payer.csv, dim_service_line.csv, dim_denial_reason.csv, claims_raw.csv

Design goals
------------
1. REPRODUCIBLE: fixed RNG seed -> identical output on every run.
2. REALISTIC ECONOMICS so the metrics are meaningful:
     - allowed = charge * payer-type contract factor  (charges are inflated list
       prices; allowed is the contracted amount). This is what makes GROSS
       collection (paid/charge) look low while NET collection (paid/allowed)
       is healthy -- the gross-vs-net teaching point.
     - denial propensity, pay lag, and contract factor all vary BY PAYER TYPE,
       so segmentation by payer reveals real, defensible patterns.
3. DELIBERATE, CONTROLLED DIRT for the data-quality stage, with ground-truth
   counts printed at the end so Stage B detection can be validated against truth.

Grain: one row per claim (header level), matching 00_schema.sql.
"""

import os
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Config -- all the knobs in one place so every number is explainable.
# --------------------------------------------------------------------------- #
SEED = 42
N_CLAIMS = 5000
AS_OF_DATE = pd.Timestamp("2025-01-15")     # AR reporting anchor (reused in SQL)
DOS_START = pd.Timestamp("2024-01-01")      # earliest date of service
DOS_END = pd.Timestamp("2025-01-10")        # latest date of service
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

rng = np.random.default_rng(SEED)

# --- Payers: canonical row + the MESSY spelling variants that land in the fact #
# Each tuple: payer_id, canonical name, payer_type, [raw spelling variants]
PAYERS = [
    ("PAY001", "Blue Cross Blue Shield", "Commercial",
     ["Blue Cross Blue Shield", "BCBS", "Blue Cross", "blue cross blue shield", "BCBS "]),
    ("PAY002", "UnitedHealthcare", "Commercial",
     ["UnitedHealthcare", "United Healthcare", "UHC", "united healthcare"]),
    ("PAY003", "Aetna", "Commercial",
     ["Aetna", "AETNA", "Aetna Inc.", "aetna"]),
    ("PAY004", "Cigna", "Commercial",
     ["Cigna", "CIGNA", "cigna health"]),
    ("PAY005", "Medicare", "Medicare",
     ["Medicare", "MEDICARE", "Medicare Part B", "medicare"]),
    ("PAY006", "Medicaid", "Medicaid",
     ["Medicaid", "MEDICAID", "State Medicaid", "medicaid"]),
    ("PAY007", "Self-Pay", "Self-Pay",
     ["Self-Pay", "Self Pay", "SELFPAY", "Patient"]),
]
# Relative frequency of each payer in the claim mix.
PAYER_WEIGHTS = np.array([0.22, 0.18, 0.13, 0.10, 0.20, 0.12, 0.05])

# Per payer TYPE behavior.
CONTRACT_FACTOR = {      # allowed / charge  (inflated charges vs contracted rate)
    "Commercial": 0.55, "Medicare": 0.35, "Medicaid": 0.28, "Self-Pay": 0.90}
DENIAL_PROB = {          # P(denied) by payer type
    "Commercial": 0.12, "Medicare": 0.08, "Medicaid": 0.18, "Self-Pay": 0.10}
PAY_LAG_MEAN = {         # mean days submission -> payment, by payer type
    "Commercial": 32, "Medicare": 26, "Medicaid": 48, "Self-Pay": 55}
PATIENT_RESP_FRAC = {    # patient share of allowed (copay/coins/deductible)
    "Commercial": 0.18, "Medicare": 0.10, "Medicaid": 0.03, "Self-Pay": 1.00}

# --- Service lines: name -> (department_group, mean charge) ----------------- #
SERVICE_LINES = {
    "Cardiology":       ("Medical",   4200),
    "Orthopedics":      ("Surgical",  9800),
    "Emergency":        ("Medical",   2600),
    "Oncology":         ("Medical",   7400),
    "Radiology":        ("Ancillary", 1300),
    "General Surgery":  ("Surgical",  8600),
    "Primary Care":     ("Medical",    480),
    "Gastroenterology": ("Medical",   3100),
}
SERVICE_LINE_NAMES = list(SERVICE_LINES.keys())
SERVICE_LINE_WEIGHTS = np.array([0.14, 0.12, 0.18, 0.08, 0.16, 0.07, 0.17, 0.08])

# --- Denial reasons: code -> (description, category, weight) ---------------- #
# Weighted so preventable FRONT-END causes (Authorization/Eligibility/Coding)
# dominate -> the category rollup tells a "most denials are preventable" story.
DENIAL_REASONS = [
    ("197", "Authorization / precert absent",        "Authorization",     0.22),
    ("27",  "Coverage terminated (eligibility)",     "Eligibility",       0.18),
    ("16",  "Claim lacks required information",       "Coding",            0.15),
    ("11",  "Diagnosis inconsistent with procedure", "Coding",            0.08),
    ("50",  "Service not medically necessary",        "Medical Necessity", 0.12),
    ("29",  "Timely filing limit expired",            "Timely Filing",     0.08),
    ("96",  "Non-covered charge",                     "Technical-Other",   0.10),
    ("18",  "Exact duplicate claim",                  "Technical-Other",   0.04),
    ("B7",  "Provider not certified for service",     "Technical-Other",   0.03),
]
REASON_CODES = [r[0] for r in DENIAL_REASONS]
REASON_WEIGHTS = np.array([r[3] for r in DENIAL_REASONS])
REASON_WEIGHTS = REASON_WEIGHTS / REASON_WEIGHTS.sum()

# Claim status mix
STATUSES = ["Paid", "Partially Paid", "Open"]   # (Denied handled via denial draw)
STATUS_WEIGHTS = np.array([0.78, 0.10, 0.12])   # among NON-denied claims

CPT_POOL = ["99213", "99214", "93000", "70450", "45378", "29881",
            "47562", "80053", "71046", "99285"]


def daterange_uniform(n, start, end):
    """n random dates uniform between start and end (inclusive-ish)."""
    span = (end - start).days
    offsets = rng.integers(0, span + 1, size=n)
    return pd.to_datetime(start) + pd.to_timedelta(offsets, unit="D")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # ---- dimension frames --------------------------------------------------
    dim_payer = pd.DataFrame(
        [(p[0], p[1], p[2]) for p in PAYERS],
        columns=["payer_id", "payer_name", "payer_type"])

    dim_service_line = pd.DataFrame(
        [(name, grp) for name, (grp, _) in SERVICE_LINES.items()],
        columns=["service_line_name", "department_group"])

    dim_denial_reason = pd.DataFrame(
        [(c, d, cat) for c, d, cat, _ in DENIAL_REASONS],
        columns=["denial_reason_code", "reason_description", "reason_category"])

    # ---- fact: claims_raw --------------------------------------------------
    n = N_CLAIMS
    claim_id = np.array([f"CLM{100000 + i}" for i in range(n)])
    patient_id = np.array([f"PT{rng.integers(1, 3200):05d}" for _ in range(n)])

    payer_idx = rng.choice(len(PAYERS), size=n, p=PAYER_WEIGHTS / PAYER_WEIGHTS.sum())
    payer_type = np.array([PAYERS[i][2] for i in payer_idx])
    # MESSY raw payer name -- pick a random spelling variant for each claim
    payer_name_raw = np.array([rng.choice(PAYERS[i][3]) for i in payer_idx])

    sl_idx = rng.choice(len(SERVICE_LINE_NAMES), size=n,
                        p=SERVICE_LINE_WEIGHTS / SERVICE_LINE_WEIGHTS.sum())
    service_line = np.array([SERVICE_LINE_NAMES[i] for i in sl_idx])
    sl_mean_charge = np.array([SERVICE_LINES[s][1] for s in service_line])

    provider_id = np.array([f"PRV{rng.integers(1, 60):03d}" for _ in range(n)])
    cpt_code = rng.choice(CPT_POOL, size=n)
    drg_code = np.where(rng.random(n) < 0.4,
                        np.array([f"{rng.integers(1, 999):03d}" for _ in range(n)]),
                        "")  # DRG only on ~40% (inpatient-ish)

    # charges: lognormal around the service-line mean
    charge_amount = np.round(
        rng.lognormal(mean=np.log(sl_mean_charge), sigma=0.35), 2)

    # contract / allowed
    contract = np.array([CONTRACT_FACTOR[t] for t in payer_type])
    allowed_amount = np.round(charge_amount * contract *
                              rng.normal(1.0, 0.05, n).clip(0.8, 1.2), 2)

    # ---- adjudication: denied? then status among the rest ------------------
    denial_p = np.array([DENIAL_PROB[t] for t in payer_type])
    denied = rng.random(n) < denial_p
    status = np.where(denied, "Denied",
                      rng.choice(STATUSES, size=n,
                                 p=STATUS_WEIGHTS / STATUS_WEIGHTS.sum()))

    denial_flag = denied.astype(int)
    # denial reason only when denied
    denial_reason_code = np.where(
        denied, rng.choice(REASON_CODES, size=n, p=REASON_WEIGHTS), "")

    # dates ------------------------------------------------------------------
    date_of_service = daterange_uniform(n, DOS_START, DOS_END)
    submit_lag = rng.integers(1, 11, size=n)          # charge-capture/coding lag
    date_submitted = date_of_service + pd.to_timedelta(submit_lag, unit="D")

    pay_lag_mean = np.array([PAY_LAG_MEAN[t] for t in payer_type])
    pay_lag = rng.gamma(shape=4.0, scale=pay_lag_mean / 4.0).round().astype(int)
    date_paid_full = date_submitted + pd.to_timedelta(pay_lag, unit="D")

    # money + dates by status
    patient_resp_frac = np.array([PATIENT_RESP_FRAC[t] for t in payer_type])
    patient_responsibility = np.round(allowed_amount * patient_resp_frac, 2)

    # collection efficiency: total payments / allowed
    coll_eff = rng.normal(0.96, 0.04, n).clip(0.80, 1.0)
    paid_full = np.round(allowed_amount * coll_eff, 2)
    coll_eff_partial = rng.normal(0.55, 0.12, n).clip(0.2, 0.8)
    paid_partial = np.round(allowed_amount * coll_eff_partial, 2)

    paid_amount = np.zeros(n)
    date_paid = [pd.NaT] * n          # object list; filled in loop, ISO-formatted later
    denial_date = [pd.NaT] * n
    adjustment_amount = np.zeros(n)
    first_pass_flag = np.zeros(n, dtype=int)
    rebill_flag = np.zeros(n, dtype=int)

    for i in range(n):
        st = status[i]
        if st == "Paid":
            paid_amount[i] = paid_full[i]
            date_paid[i] = date_paid_full[i]
            adjustment_amount[i] = round(charge_amount[i] - allowed_amount[i], 2)
        elif st == "Partially Paid":
            paid_amount[i] = paid_partial[i]
            date_paid[i] = date_paid_full[i]
            adjustment_amount[i] = round(charge_amount[i] - allowed_amount[i], 2)
        elif st == "Denied":
            paid_amount[i] = 0.0
            allowed_amount[i] = 0.0          # denied -> nothing allowed
            patient_responsibility[i] = 0.0
            adjustment_amount[i] = 0.0
            denial_date[i] = date_submitted[i] + pd.Timedelta(days=int(rng.integers(5, 30)))
        else:  # Open -- billed, not yet adjudicated; sits in AR
            paid_amount[i] = 0.0
            date_paid[i] = pd.NaT

    # clean-claim & rebill flags (correlated with denial)
    base_clean_p = np.where(denied, 0.25, 0.92)
    first_pass_flag = (rng.random(n) < base_clean_p).astype(int)
    rebill_p = np.where(first_pass_flag == 0, 0.6, 0.05)
    rebill_flag = (rng.random(n) < rebill_p).astype(int)

    df = pd.DataFrame({
        "claim_id": claim_id,
        "patient_id": patient_id,
        "payer_name_raw": payer_name_raw,
        "service_line": service_line,
        "provider_id": provider_id,
        "cpt_code": cpt_code,
        "drg_code": drg_code,
        "date_of_service": date_of_service,
        "date_submitted": date_submitted,
        "date_paid": date_paid,
        "denial_date": denial_date,
        "charge_amount": charge_amount,
        "allowed_amount": allowed_amount,
        "paid_amount": np.round(paid_amount, 2),
        "adjustment_amount": np.round(adjustment_amount, 2),
        "patient_responsibility": patient_responsibility,
        "claim_status": status,
        "denial_flag": denial_flag,
        "denial_reason_code": denial_reason_code,
        "first_pass_flag": first_pass_flag,
        "rebill_flag": rebill_flag,
    })

    # ======================================================================= #
    # SEEDED DIRT -- controlled, counted, validated against in Stage B.
    # ======================================================================= #
    dirt = {}

    # 1. Missing date_paid on PAID claims (status says paid, no pay date).
    paid_mask = df["claim_status"].isin(["Paid", "Partially Paid"]).values
    paid_idx = np.where(paid_mask)[0]
    n_miss_paid = int(0.03 * len(paid_idx))
    miss_paid = rng.choice(paid_idx, size=n_miss_paid, replace=False)
    df.loc[miss_paid, "date_paid"] = pd.NaT
    dirt["missing_date_paid_on_paid"] = n_miss_paid

    # 2. Missing denial_reason_code on DENIED claims.
    den_idx = np.where(df["denial_flag"].values == 1)[0]
    n_miss_reason = int(0.05 * len(den_idx))
    miss_reason = rng.choice(den_idx, size=n_miss_reason, replace=False)
    df.loc[miss_reason, "denial_reason_code"] = ""
    dirt["missing_denial_reason_on_denied"] = n_miss_reason

    # 3. Impossible dates: date_paid < date_of_service.
    payable = np.where(df["date_paid"].notna().values)[0]
    n_bad_date = max(8, int(0.003 * n))
    bad_date = rng.choice(payable, size=n_bad_date, replace=False)
    df.loc[bad_date, "date_paid"] = (
        df.loc[bad_date, "date_of_service"] - pd.to_timedelta(
            rng.integers(1, 20, size=n_bad_date), unit="D"))
    dirt["date_paid_before_service"] = n_bad_date

    # 4. Negative or zero charges.
    n_bad_charge = max(6, int(0.002 * n))
    bad_charge = rng.choice(n, size=n_bad_charge, replace=False)
    df.loc[bad_charge, "charge_amount"] = rng.choice([0.0, -100.0, -250.0],
                                                     size=n_bad_charge)
    dirt["nonpositive_charge"] = n_bad_charge

    # 5. Duplicate claim_ids: append exact-copy rows for ~0.5% of claims.
    n_dup = max(10, int(0.005 * n))
    dup_src = rng.choice(n, size=n_dup, replace=False)
    dups = df.iloc[dup_src].copy()
    df = pd.concat([df, dups], ignore_index=True)
    dirt["duplicate_claim_id_rows"] = n_dup

    # (6. Inconsistent payer spellings are PERVASIVE by construction -- see
    #     payer_name_raw variants above, not a post-hoc injection.)

    # ---- format dates as ISO TEXT; NaT -> empty string (loads as NULL) -----
    for col in ["date_of_service", "date_submitted", "date_paid", "denial_date"]:
        df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d").fillna("")

    # ---- write CSVs --------------------------------------------------------
    dim_payer.to_csv(os.path.join(OUT_DIR, "dim_payer.csv"), index=False)
    dim_service_line.to_csv(os.path.join(OUT_DIR, "dim_service_line.csv"), index=False)
    dim_denial_reason.to_csv(os.path.join(OUT_DIR, "dim_denial_reason.csv"), index=False)
    df.to_csv(os.path.join(OUT_DIR, "claims_raw.csv"), index=False)

    # ---- ground-truth report (Stage B validates detection against this) ----
    print("=" * 64)
    print("SYNTHETIC DATA GENERATED")
    print("=" * 64)
    print(f"AS_OF_DATE (AR anchor): {AS_OF_DATE.date()}")
    print(f"claims_raw rows (incl. {dirt['duplicate_claim_id_rows']} dup rows): {len(df)}")
    print(f"unique claim_id        : {df['claim_id'].nunique()}")
    print("\nclaim_status mix:")
    print(df["claim_status"].value_counts().to_string())
    print(f"\ndenial_flag = 1        : {int(df['denial_flag'].sum())} "
          f"({df['denial_flag'].mean():.1%})")
    print("\n--- GROUND-TRUTH SEEDED DIRT (validate Stage B against these) ---")
    for k, v in dirt.items():
        print(f"  {k:34s}: {v}")
    print("=" * 64)
    print("Wrote: dim_payer.csv, dim_service_line.csv, dim_denial_reason.csv, "
          "claims_raw.csv -> data/raw/")


if __name__ == "__main__":
    main()
