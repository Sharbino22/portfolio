# Cardiovascular Risk Management Among US Cancer Survivors
## A Population-Based Study Using NHANES 1999-2018

**Author:** Sridharan (Shri) Gopalsamy Ramaswamy, MPH/MBA
**Affiliation:** Washington University in St. Louis, Siteman Cancer Center
**Date:** April 2026

---

## Research Question

Among US adults with hypertension or diabetes, do cancer survivors achieve better or worse cardiovascular risk control than non-cancer adults? Does depression modify this relationship?

## Headline Finding

**Cancer survivors have 26% higher odds of controlled blood pressure and 33% higher odds of controlled A1c than non-cancer adults with the same conditions.** The expected care gap doesn't show up in the data. Instead, the regular healthcare contact from cancer surveillance appears to spill over into better chronic disease management.

| Outcome | Sample | Adjusted OR (95% CI) | p |
|---|---|---|---|
| BP controlled | Hypertensives (n = 11,772) | **1.26 (1.10, 1.44)** | 0.001 |
| A1c controlled | Diabetics (n = 5,194) | **1.33 (1.03, 1.72)** | 0.031 |
| Total cholesterol >= 240 | All (n = 32,110) | 0.86 (0.71, 1.04) | 0.111 |

The cancer x depression interaction was not statistically significant for any outcome (all p > 0.09), suggesting depression does not erode the survivor advantage.

## Data

- **NHANES 1999-2018**, 10 cycles, n = 51,168 adults including 4,715 cancer survivors
- Models including depression are restricted to cycles **2005-2018** because PHQ-9 was not collected before 2005
- Outcome variables derived from BPX (blood pressure exam), TCHOL (total cholesterol), GHB (HbA1c), BPQ (medication questionnaire), DPQ (PHQ-9 depression screener)

## Methods

- Survey-weighted logistic regression via `statsmodels.GLM(family=Binomial)`
- Weights normalized so effective N matches actual N (pseudo-likelihood)
- Cluster-robust SEs clustered on combined `SDMVSTRA x SDMVPSU` strata to approximate Taylor-series linearization
- Each model adjusts for age, sex, race/ethnicity, smoking, obesity, depression, with a cancer x depression interaction
- Cycle-stratified models test the temporal stability of the cancer effect

## Interactive Dashboard

A single-file Plotly.js dashboard ships alongside the static figures:

**`dashboard.html`** — self-contained HTML (~100 KB) with embedded JSON. Pre-aggregated 1,483 group records (cancer × age × sex × race × cycle × depressed) computed in Python, then filtered and weighted in the browser. Includes:
- Hero comparison bars (BP / A1c / cholesterol control rates, cancer vs non-cancer)
- BP and A1c control trends across 10 NHANES cycles
- Sample composition by age × cancer status
- Filters: age group, sex, race/ethnicity dropdowns + a "Split by PHQ-9" depression toggle that splits every chart by depressed yes/no
- Reachable from `cv-risk-gaps.html` via the "Launch Interactive Dashboard" button under the hero subtitle, and from the homepage project card via the green "Live Dashboard" badge

## Files

```
cv-risk-gaps/
├── README.md
├── CLAUDE.md
├── dashboard.html                 (interactive Plotly dashboard, single file)
├── docs/
│   └── PROJECT_WALKTHROUGH.md
├── data/
│   └── tableau_export.csv         (51,168 rows x 15 cols, ready for dashboards;
│                                    binary cols recoded to readable string labels)
├── figures/
│   ├── forest_cancer_effect.png
│   ├── control_rates_by_cancer.png
│   ├── trend_bp_control_by_cycle.png
│   └── card_cv_risk_gaps.png      (portfolio card image)
└── scripts/
    └── build_assets.py            (regenerates all figures and exports)
```

## Reproducing the analysis

The upstream analysis lives in `Projects/nhanes-cancer-survival/scripts/cv_risk_gaps.py`. This project consumes its outputs from `Projects/nhanes-cancer-survival/analysis/cv_risk_gaps/`. To rebuild figures and the Tableau export:

```bash
cd Projects/cv-risk-gaps
python3 scripts/build_assets.py
```
