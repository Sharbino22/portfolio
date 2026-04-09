# Medicare Rate & Utilization Analysis

**Author:** Sridharan Gopalsamy Ramaswamy | [sridharanshri.com](https://sridharanshri.com)  
**Data:** CMS Medicare Public Use Files (2022)  
**Tools:** Python, pandas, numpy, matplotlib, python-docx

---

## Business Question

How do Medicare payment rates and utilization patterns vary across providers,
procedures, and geographies for high-cost conditions, and what does this imply
for payer contracting strategy?

---

## Key Findings

- **5.4x median markup**: Hospitals charge 5.4x what Medicare pays, but the ratio spans 1.2x (Maryland) to 10.7x (Nevada), a 9.5x spread driven by state regulatory environments
- **Septicemia dominates volume**: 550K discharges (11% of all Medicare inpatient stays), the top target for bundled payment contracts
- **$295K per case**: Heart transplants lead cost. A 10% rate difference = $30K per case for commercial payers benchmarking against Medicare
- **Specialty markup variation**: Physician markups range from ~2x to 5x depending on specialty, signaling where rate negotiations have the most room
- **Volume-cost mismatch**: Lab/radiology drive spend through utilization; surgery drives it through unit price. Different contracting levers apply.

---

## Data

| Dataset | Source | Records | Year |
|---------|--------|---------|------|
| Medicare Inpatient Hospitals by Provider and Service | [data.cms.gov](https://data.cms.gov) | 145,742 | 2022 |
| Medicare Physician & Other Practitioners by Provider and Service | [data.cms.gov](https://data.cms.gov) | 9,755,020 | 2022 |

Combined scope: 3,015 hospitals, 1.15M physician NPIs, 533 DRGs, 6,326 HCPCS codes, 51 states.

Run `python download_data.py` to download both datasets automatically.

---

## Methods and Decisions

### 1. Data Acquisition (`download_data.py`)
- Direct download from CMS public file endpoints with progress tracking
- URLs point to the CMS `sites/default/files` CDN with UUID-prefixed paths (CMS re-releases datasets periodically under new paths)
- Fallback instructions included for manual download if URLs expire

### 2. Data Preparation (`01_data_prep.ipynb`)
- **Encoding**: CMS files use Latin-1 encoding (not UTF-8). Detected via trial after initial `UnicodeDecodeError`
- **Deduplication**: Checked on natural keys (CCN + DRG for inpatient, NPI + HCPCS + Place of Service for physician). Zero duplicates found
- **Column drops**: Removed high-missingness non-analytical columns (middle initial, address line 2, credentials) from physician file
- **Geographic filter**: Dropped 407 non-US rows from physician file (territories and foreign providers)
- **Derived variable**: `markup_ratio = submitted charges / Medicare payment` added to both datasets
- **Type enforcement**: Zip codes and HCPCS codes read as strings to preserve leading zeros

### 3. Utilization Analysis (`02_utilization.ipynb`)
- Top 15 DRGs ranked by discharge volume and average Medicare payment
- DRG-level markup ratios for high-volume procedures (>5,000 discharges)
- State-level aggregation: total discharges, average payment, provider count
- Within-state payment distribution via box plots (outliers excluded for readability)
- Top 15 physician specialties by service volume and per-service cost

### 4. Rate Variation Analysis (`03_rate_variation.ipynb`)
- Scatter plots: charges vs. payment colored by markup ratio (sampled for performance)
- Markup distribution histogram with median annotation
- State-level markup with IQR error bars and national median reference line
- HCPCS-level coefficient of variation to identify highest-variation procedures (filtered: >500 records, >$50 mean payment)
- Specialty-level markup ranking with conditional coloring (amber for >3x)
- Three-layer state rate spread: submitted charge, Medicare allowed, Medicare payment

### 5. Case Study Narrative (`04_case_study.ipynb`)
- Executive summary with three headline findings
- Eight analysis sections, each with inline figures and "so what" for a payer strategy audience
- Strategic implications table mapping findings to contracting levers
- Full methods documentation

### 6. Word Document (`docs/case_study.docx`)
- Generated programmatically via python-docx (`build_docx.py`)
- All 14 figures embedded at print quality
- Formatted with tables, headings, and figure captions

---

## Figures (14 total)

| Category | Figures |
|----------|---------|
| Utilization | Top 15 DRGs by volume, Top 15 DRGs by cost, DRG markup ratios |
| Geographic | State volume + payment, State payment box plot, State markup variation |
| Physician | Top 15 specialties by volume, Top 15 specialties by cost |
| Rate Variation | Inpatient charges vs. payment, Markup distribution, Physician charges vs. allowed, Specialty markup ratios, HCPCS payment variation, State physician rate spread |

---

## Project Structure

```
medicare-claims-analysis/
  README.md                 <- This file
  CLAUDE.md                 <- AI assistant context
  download_data.py          <- Data download script
  build_docx.py             <- Word document generator
  data/
    raw/                    <- Downloaded CSVs (not committed)
    processed/              <- Cleaned outputs from 01_data_prep
  notebooks/
    01_data_prep.ipynb      <- Load, clean, validate
    02_utilization.ipynb    <- Volume, cost, geography
    03_rate_variation.ipynb <- Payment vs. charges, markup, spread
    04_case_study.ipynb     <- Full narrative with inline figures
  figures/                  <- All PNGs at 150 dpi
  docs/
    case_study.docx         <- Final Word document
```

---

## Setup

```bash
pip install pandas numpy matplotlib python-docx jupyter
python download_data.py
jupyter notebook notebooks/
```

---

## Relevance

This project demonstrates:
- Hands-on experience with Medicare administrative claims data
- Fluency with ICD/DRG/HCPCS coding structures
- Payer-provider rate dynamics and cost variation analysis
- Translating claims data into strategic insights for health plans and providers

Directly relevant to roles in health plan analytics, HEOR consulting, payer-provider rate benchmarking (e.g., Deloitte ConvergeHEALTH / MyRateFinder), and healthcare strategy.
