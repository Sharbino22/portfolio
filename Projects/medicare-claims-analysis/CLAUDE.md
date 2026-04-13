# Project: Medicare Rate & Utilization Analysis
**Owner:** Sridharan Gopalsamy Ramaswamy | sridharanshri.com
**Status:** [ ] In Progress | [ ] Complete

---

## Research Question
How do Medicare payment rates and utilization patterns vary across providers,
procedures, and geographies for high-cost conditions — and what does this
imply for payer contracting strategy?

---

## Datasets
| File | Source | Format | Notes |
|------|--------|--------|-------|
| Medicare Inpatient Hospital PUF | data.cms.gov | CSV | DRG-level, provider, payments |
| Medicare Physician & Other Practitioners PUF | data.cms.gov | CSV | HCPCS-level, specialty, payments |

Download via: `python download_data.py`
Data lands in: `/data/raw/`

---

## Key Variables
- `drg_definition` — MS-DRG code and description
- `hcpcs_code` / `hcpcs_description` — procedure codes
- `provider_state` — geography
- `total_discharges` — utilization volume
- `average_covered_charges` — what providers billed
- `average_total_payments` — what Medicare actually paid
- `average_medicare_payments` — Medicare's share
- `provider_type` / `provider_specialty` — provider classification

---

## Methods (in order)
1. Data download and validation (`download_data.py`)
2. Cleaning, deduplication, missingness check (`01_data_prep.ipynb`)
3. Utilization analysis — top DRGs, LOS, volume by geography (`02_utilization.ipynb`)
4. Rate variation — payment vs. charges, spread by payer type, geography (`03_rate_variation.ipynb`)
5. Case study narrative with inline figures (`04_case_study.ipynb`)

---

## File Map
```
medicare-claims-analysis/
  CLAUDE.md               ← You are here. Read this first every session.
  download_data.py        ← Run once to get data
  README.md               ← Public-facing project summary
  dashboard.html          ← Single-file Plotly.js interactive explorer (embedded JSON)
  data/
    raw/                  ← Downloaded CSVs (do not commit to GitHub)
    processed/            ← Cleaned files output by 01_data_prep
  notebooks/
    01_data_prep.ipynb    ← Load, clean, validate CMS data
    02_utilization.ipynb  ← Volume, cost, LOS by DRG/HCPCS/geography
    03_rate_variation.ipynb ← Payment vs. charges, markup ratio, spread
    04_case_study.ipynb   ← Portfolio narrative, key figures inline
  figures/                ← All saved PNGs (used in Word doc + portfolio)
  docs/
    case_study.docx       ← Final Word document (created at end)
```

---

## Critical Rules for Claude Code
- **Never read full CSVs into context.** Use `df.head(10)`, `df.dtypes`, `df.shape` only.
- **Save all key figures** to `/figures/` as PNG at 150 dpi minimum.
- **No debug prints** in final notebook outputs — clean cells only.
- **Each notebook is self-contained** — import and load at top of each one.
- **Processed data** (cleaned CSVs) saved to `/data/processed/` by notebook 01,
  used by notebooks 02-04.

---

## Key Findings
- Hospitals charge a median 5.4x what Medicare pays, but the ratio spans 1.2x (MD) to 10.7x (NV), a 9.5x spread driven by state regulatory environments
- Septicemia accounts for 550K discharges (11% of Medicare inpatient volume); heart transplants lead cost at ~$295K/case
- Physician markup varies sharply by specialty (median 2.8x overall), with high-variation HCPCS codes identifiable for outlier benchmarking
- Volume-cost mismatch across specialties: lab/radiology drive spend through utilization, surgery through unit price
- Top 5 DRGs account for >25% of all inpatient volume, making them priority targets for bundled payment contracts

---

## Target Roles This Project Supports
- ConvergeHEALTH / MyRateFinder (Deloitte) — payer-provider rate analytics
- Health plan analytics roles — claims data fluency
- HEOR consulting — cost variation, utilization modeling
- Healthcare strategy — financial and operational insights

---

## End-of-Project Checklist
- [x] All 4 notebooks complete and outputs clean
- [x] Figures saved to /figures/ (14 key visuals)
- [x] Key findings documented in this file (above)
- [x] case_study.docx created in /docs/
- [x] Portfolio HTML (index.html) updated with new project card
- [x] README.md finalized
- [x] Standalone case-study page (`medicare-analysis.html`) live
- [x] Interactive Plotly dashboard (`dashboard.html`) shipped, linked from case-study hero and homepage card via amber "Live Dashboard" badge
- [ ] GitHub repo pushed
- [ ] sridharanshri.com project card live
