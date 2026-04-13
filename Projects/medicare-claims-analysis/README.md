# Medicare Rate & Utilization Analysis

**Author:** Sridharan Gopalsamy Ramaswamy | [sridharanshri.com](https://sridharanshri.com)
**Data:** CMS Medicare Public Use Files (Calendar Year 2022)
**Tools:** Python, pandas, numpy, matplotlib, python-docx
**Status:** Complete — 4 notebooks + Word case study + interactive dashboard

> **About this README.** This document is a step-by-step decision log of how the analysis was actually built, with the numbers, the dead ends, and the why-this-not-that for each step. If you're skimming, the headline lives in "The one-sentence version" below. If you need to reproduce or defend the work months from now, read the step log.

---

## The one-sentence version

US hospitals charge a national median of **5.4x what Medicare actually pays**, but the markup ranges from **1.2x in Maryland to 10.7x in Nevada** — a 9.5x spread driven by state regulatory environments, not by procedure mix or provider type. That's a payer contracting story, not a clinical one.

---

## Why this matters

Hospitals set their own chargemasters. Medicare reimburses on a fixed schedule. The gap between those two numbers is one of the most cited indicators of US healthcare pricing opacity, and it's the foundation of any commercial-payer rate benchmarking strategy. If you know that hospitals in your network are 5x'ing Medicare on average but the all-payer-rate-setting state next door is at 1.2x, you have a defensible anchor for the next round of contract negotiations.

---

## Headline numbers

- **3,015 hospitals** in the inpatient file, **1.15M physician NPIs** in the physician file
- **5.0M Medicare discharges** and **2.5B physician services** modeled
- **Median inpatient markup: 5.4x** (charges / Medicare payment)
- **State markup spread: 1.2x (MD) → 10.7x (NV)**, a 9.5x range
- **Septicemia is the single highest-volume DRG**: 550K discharges, ~11% of all Medicare inpatient stays
- **Costliest DRG: heart transplants** at ~$295K average payment per case

---

## Data

| Dataset | Source | Records | Year |
|---|---|---:|---|
| Medicare Inpatient Hospitals by Provider and Service | [data.cms.gov](https://data.cms.gov) | 145,742 | 2022 |
| Medicare Physician & Other Practitioners by Provider and Service | [data.cms.gov](https://data.cms.gov) | 9,755,427 | 2022 |

After cleaning: **145,742 inpatient rows × 16 cols** and **9,755,020 physician rows × 24 cols** across 51 US states. Combined raw scope: **~9.9M rows, ~2.9 GB** of cleaned CSV.

Run `python download_data.py` to fetch both datasets directly from the CMS public file CDN.

---

## Step-by-step log

### Step 1: Download both PUF files (`download_data.py`)

- Pulled both files directly from the CMS `sites/default/files` CDN with progress tracking
- CMS re-releases the same datasets periodically under new UUID-prefixed paths, so the URLs in the script have a finite shelf life. Manual-download fallback instructions are included as comments in the script in case the URLs expire later
- Downloaded files land in `data/raw/` (gitignored — they're 2.9 GB combined)

**Decision:** A separate download script (rather than embedding the URLs in notebook 01) so the data acquisition step is self-contained, idempotent, and easy to re-run when CMS updates the files.

### Step 2: Load the inpatient PUF and discover the encoding gotcha (`01_data_prep.ipynb` §1)

- Initial `pd.read_csv` on the inpatient file raised `UnicodeDecodeError`. CMS does NOT use UTF-8 — these files are **Latin-1** encoded. After switching to `encoding='latin-1'` the load succeeded
- Raw shape: `(145742, 15)` — that's hospital × DRG combinations, not unique hospitals (3,015 unique CCNs across 533 DRGs)
- Columns are CMS-style ALL_CAPS_UNDERSCORE with `Rndrng_Prvdr_*` prefixes (e.g., `Rndrng_Prvdr_CCN`, `Avg_Submtd_Cvrd_Chrg`). Unreadable as-is

**Decision:** Document the Latin-1 encoding requirement loudly in CLAUDE.md so future-me doesn't burn 20 minutes on the same error.

### Step 3: Inpatient missingness, dedup, and rename (`01_data_prep.ipynb` §1a-c)

- Only 2 columns had any missingness: `Rndrng_Prvdr_RUCA` and `Rndrng_Prvdr_RUCA_Desc`, 677 rows each (~0.5%). RUCA is rurality classification, so this is fine to leave as NaN — most analyses use state, not RUCA
- Checked for duplicates on the natural key `(CCN, DRG)`: **0 duplicates**. The CMS file is already at the right grain
- Renamed all columns to readable snake_case (`provider_ccn`, `drg_code`, `total_discharges`, `avg_covered_charges`, `avg_total_payments`, `avg_medicare_payments`)
- Derived `markup_ratio = avg_covered_charges / avg_medicare_payments` — the headline metric for the whole project
- Final inpatient shape: `(145742, 16)`

**Decision:** Markup ratio defined as charges-over-payment (not the inverse) so values >1 are intuitive: "charges are X times what Medicare paid."

### Step 4: Load the physician PUF and discover it's an order of magnitude bigger (`01_data_prep.ipynb` §2)

- Raw shape: `(9755427, 28)` — 9.76 million rows. Loading takes ~30 seconds and uses several GB of RAM
- 28 columns with the same `Rndrng_Prvdr_*` ugliness, plus HCPCS-specific fields (`HCPCS_Cd`, `HCPCS_Desc`, `HCPCS_Drug_Ind`, `Place_Of_Srvc`)
- Heavy missingness on **non-essential** identification columns: `Rndrng_Prvdr_MI` (3.4M missing), `Rndrng_Prvdr_St2` (7.2M missing — most providers don't have an address line 2), `Rndrng_Prvdr_Crdntls` (1M)
- A handful of structurally important columns missing for very few rows: `Rndrng_Prvdr_State_FIPS` missing for 3, `Rndrng_Prvdr_RUCA` missing for ~12K

**Decision:** Drop the high-missingness identification columns (`MI`, `St2`, `Crdntls`, `St1`, `Cntry`) since they don't matter for any payment analysis. Saves memory and removes noise. Down from 28 → 24 columns.

### Step 5: Physician dedup and US filter (`01_data_prep.ipynb` §2c-d)

- Checked for duplicates on the natural key `(NPI, HCPCS_Cd, Place_Of_Srvc)`: **0 duplicates**
- Geographic filter: dropped **407 non-US rows** (territories like PR, GU, VI plus a handful of foreign providers reported in the file). Final state count: 51 (50 + DC), down from 61 in the raw file
- Renamed columns to snake_case
- Derived `markup_ratio = avg_submitted_charge / avg_medicare_payment` (same convention as inpatient)
- Final physician shape: `(9755020, 24)`

**Decision:** Restrict to US states only because every downstream analysis is state-stratified. Including territories would create misleading "states" with tiny n. Note this drops <0.005% of rows.

### Step 6: Save cleaned files and quick validation (`01_data_prep.ipynb` §3-4)

- `inpatient_clean.csv` saved at **38.9 MB**
- `physician_clean.csv` saved at **2,849.3 MB** — neither file is committed to git
- Validation summary printed: missingness now 0.06% inpatient and 0.24% physician (both essentially clean)

### Step 7: Top DRGs by volume (`02_utilization.ipynb` §2)

- Aggregated by `drg_code, drg_desc`, summing `total_discharges` and computing volume-weighted means for the payment columns
- Top 15 by discharge volume saved to `figures/top15_drg_volume.png`
- **Finding: septicemia DRG 871 ("Septicemia or severe sepsis without MV >96 hours with MCC") has 550,306 discharges**, making it the single largest line item in Medicare inpatient volume — about 11% of all 5M discharges

**Why this matters:** Any value-based contract that doesn't explicitly carve out sepsis pathways is leaving the highest-volume condition unmanaged.

### Step 8: Top DRGs by cost (`02_utilization.ipynb` §3-4)

- Re-ranked the same data by `avg_medicare_payments`, top 15 saved to `figures/top15_drg_cost.png`
- **Finding: heart transplants and ECMO cases lead at ~$295K and ~$178K per case** average Medicare payment
- DRG markup ratios figure: scatter of charges vs payment with markup color coding, saved as `figures/drg_markup_ratios.png`. Confirms the nonlinear pattern — markup compresses for high-cost DRGs and is widest for cheap procedures

**Decision:** Show two separate top-15 charts (volume and cost) instead of one combined view, because the two rankings barely overlap. Septicemia is high-volume but mid-cost; transplants are high-cost but low-volume. Conflating them obscures both stories.

### Step 9: Geographic state aggregation (`02_utilization.ipynb` §5-6)

- State-level aggregates: total discharges, volume-weighted average payment, hospital count
- Two figures: `state_volume_payment.png` (combined volume + payment view) and `state_payment_boxplot.png` (within-state distribution for top 10 states by volume)
- Hit a `MatplotlibDeprecationWarning` on `boxplot(labels=...)` — the parameter renamed to `tick_labels` in 3.9. Left as a deprecation, not an error, will fix on next run

**Finding:** California, Texas, and Florida lead in both volume and payment magnitude, but the state-level *spread* of markup (next step) is where the real story is.

### Step 10: Top physician specialties (`02_utilization.ipynb` §7-8)

- Top 15 by total service volume → `top15_specialty_volume.png`
- Top 15 by per-service cost → `top15_specialty_cost.png`
- **Volume leaders:** Clinical Laboratory (314M services), Hematology/Oncology, Diagnostic Radiology
- **Cost leaders:** Ambulatory surgical centers, cardiac surgery, high-end procedures

**Decision worth noting:** The volume vs cost dichotomy is the foundation of the "different contracting levers" point in the case study — utilization management for high-volume/low-cost specialties (lab, radiology), rate negotiation for low-volume/high-cost specialties (surgery, transplant). Two different playbooks.

### Step 11: Inpatient markup distribution and the state-level spread (`03_rate_variation.ipynb` §2-4)

- Charges vs Medicare payment scatter (sampled for performance — full 145K-point scatter is unreadable) → `inpatient_charges_vs_payment.png`
- Markup distribution histogram with median annotation → `inpatient_markup_distribution.png`. **Median 5.4x**, right-skewed with a tail extending to 12-15x for outlier hospitals
- State markup ranking with IQR error bars and national median reference → `state_markup_variation.png`
- **The headline finding lives here:** Maryland's median is 1.2x. Nevada's median is 10.7x. That's a 9.5x spread on the same underlying clinical care

**Why MD is the outlier:** Maryland is the only US state operating an **all-payer rate-setting system**. Hospital charges and payments are regulated to be roughly equivalent across all payers (Medicare, Medicaid, commercial). The 1.2x is by design, not by coincidence. Every other state in the analysis is either light-touch or fully market-based.

**Decision:** Lead the case study with the MD/NV comparison because it makes the point in 8 words and survives any audience: clinical, finance, policy, or executive.

### Step 12: HCPCS-level variation (`03_rate_variation.ipynb` §5-6)

- Computed coefficient of variation (CoV) of `avg_medicare_payment` per HCPCS code, filtered to procedures with >500 records and >$50 mean payment so noise doesn't dominate
- Highest-variation HCPCS codes saved to `figures/hcpcs_payment_variation.png`
- **Finding:** Same procedure code can have 3-5x payment variation across providers, signaling specific line items where outlier benchmarking would surface mispriced contracts

### Step 13: Specialty-level markup ranking (`03_rate_variation.ipynb` §7)

- Volume-weighted markup ratio by specialty → `specialty_markup_ratio.png`
- Conditional coloring: amber for specialties >3x markup
- Range: ~2x (lower end) to ~5x (higher end) depending on specialty mix

### Step 14: State-level physician rate spread (`03_rate_variation.ipynb` §8)

- Three-layer bar chart per state: submitted charges, Medicare-allowed amount, Medicare payment → `state_physician_rate_spread.png`
- Pattern: the gap between submitted and allowed is roughly constant in proportion across states, but the *absolute* dollar levels vary. CA, NY, NJ have both high charges AND high payments — those are the states with the biggest dollar opportunity for commercial rate benchmarking

### Step 15: Case study narrative (`04_case_study.ipynb`)

- Executive summary, eight analysis sections, each with embedded figures and a "Takeaway for payer strategy" callout
- Strategic implications table mapping each finding to a contracting lever (bundled payment, percent-of-Medicare benchmarking, multi-state playbooks, outlier surfacing, utilization management vs rate negotiation)
- Methods documentation at the bottom for reproducibility

**Decision:** Audience is HEOR consultants and payer-side strategy folks, not clinicians. The narrative leans on dollar impact and contracting levers, not clinical interpretation.

### Step 16: Word document export (`build_docx.py`)

- Generated programmatically via `python-docx`
- All 14 figures embedded at print resolution
- Tables, headings, captions formatted to match the WashU MBA case study template
- Output: `docs/case_study.docx`

**Decision:** Build the docx programmatically so updating a number doesn't mean opening Word and manually re-pasting figures. Run `python build_docx.py` and the whole document regenerates.

### Step 17: Interactive dashboard (`dashboard.html`)

- Single-file Plotly.js explorer (~322 KB) with embedded JSON
- Server-side aggregation in Python: state-level metrics, top 30 national + top 15 per-state DRGs, top specialties, top HCPCS codes
- US choropleth, click-to-drill into state, dataset toggle (inpatient/physician), top-N metric switcher (markup / volume / charge / payment), markup-vs-volume scatter
- Linked from `medicare-analysis.html` (case study page) and from the homepage card via the amber "Live Dashboard" badge

---

## Strategic implications (the case study payoff)

| Finding | Strategic implication |
|---|---|
| Septicemia = 11% of inpatient volume | Bundled payment and readmission reduction programs should prioritize sepsis pathways |
| Median inpatient markup = 5.4x | Chargemaster-based contracts systematically overpay vs Medicare; percent-of-Medicare benchmarks are more defensible |
| MD vs NV markup spread = 9.5x | State regulatory environment is a first-order variable; multi-state payers need state-specific playbooks |
| High-variation HCPCS codes (CoV > 0.5) | Procedure-level benchmarking can surface outlier providers billing 3-5x peers for the same service |
| Volume-cost specialty mismatch | Utilization management for high-volume/low-cost specialties; rate negotiation for high-cost ones |

---

## Figures (14 total)

| Category | Files |
|---|---|
| Inpatient utilization | `top15_drg_volume.png`, `top15_drg_cost.png`, `drg_markup_ratios.png` |
| Inpatient geography | `state_volume_payment.png`, `state_payment_boxplot.png`, `state_markup_variation.png` |
| Inpatient rate variation | `inpatient_charges_vs_payment.png`, `inpatient_markup_distribution.png` |
| Physician utilization | `top15_specialty_volume.png`, `top15_specialty_cost.png` |
| Physician rate variation | `physician_charges_vs_allowed.png`, `hcpcs_payment_variation.png`, `specialty_markup_ratio.png`, `state_physician_rate_spread.png` |

---

## Project structure

```
medicare-claims-analysis/
  README.md                       <- This file (step-by-step log)
  CLAUDE.md                       <- AI assistant context + workflow rules
  download_data.py                <- Run once to fetch CMS data
  build_docx.py                   <- Generates case_study.docx from notebooks + figures
  dashboard.html                  <- Single-file Plotly interactive explorer
  data/
    raw/                          <- Downloaded CSVs (NOT committed, 2.9 GB)
    processed/
      inpatient_clean.csv         (39 MB)
      physician_clean.csv         (2.85 GB, also gitignored)
  notebooks/
    01_data_prep.ipynb            <- Load, encode-fix, dedup, rename, derive markup
    02_utilization.ipynb          <- Top DRGs, top specialties, geographic volume
    03_rate_variation.ipynb       <- Markup distribution, state spread, HCPCS CoV
    04_case_study.ipynb           <- Narrative with inline figures
  figures/                        <- 14 PNGs at 150 dpi
  docs/
    case_study.docx               <- Final Word document (built by build_docx.py)
```

---

## Limitations

1. **2022 data only.** No time-series. The MD/NV gap could be widening or narrowing — this analysis is a snapshot, not a trend.
2. **PUF aggregation.** CMS suppresses provider-DRG combinations with <11 cases for privacy. The high-volume DRGs are intact but the long tail is censored.
3. **Markup ratio is a directional indicator, not a causal measure.** It conflates chargemaster strategy, payer mix, case complexity, and provider negotiating power. Useful for surfacing outliers, not for assigning blame.
4. **Self-reported volume.** `total_discharges` and `total_services` are what providers reported to CMS. No claims-level audit.
5. **No commercial-payer comparison.** The analysis benchmarks against Medicare. The actual rate gap commercial payers are paying is *outside* this dataset and would require something like Health Care Cost Institute or all-payer claims data.

---

## What I'd do differently next time

- Add 2018-2022 time series to test whether state-level markups are stabilizing under transparency regulations
- Pull NPI specialty taxonomy to slice physician markups by individual rather than self-reported specialty (catches gaming)
- Cross-walk DRGs to commercial APR-DRGs for like-for-like comparison
- Include the Hospital Price Transparency machine-readable files (when CMS finishes the federation work)

---

## Relevance

This project demonstrates:
- Hands-on experience with Medicare administrative claims at full PUF scale (9.9M rows)
- Fluency with DRG/HCPCS coding structures
- Payer-provider rate dynamics framed for a strategy audience
- Translating raw claims into specific contracting recommendations
- Building polished deliverables (Word case study + interactive dashboard) on top of the analysis

Directly relevant to roles in health plan analytics, HEOR consulting (payer-provider rate benchmarking — e.g. Deloitte ConvergeHEALTH / MyRateFinder), Milliman, and healthcare strategy at insurers or provider systems.

---

## Setup

```bash
pip install pandas numpy matplotlib python-docx jupyter plotly
python download_data.py
jupyter notebook notebooks/
```

---

*Sridharan Gopalsamy Ramaswamy | MPH/MBA, Washington University in St. Louis*
