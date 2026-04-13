# CV Risk Gaps Project — Context File

## Project Goal
Quantify whether US cancer survivors achieve better or worse cardiovascular risk
control (BP, A1c, cholesterol) than non-cancer adults with the same underlying
conditions, using survey-weighted logistic regression on NHANES 1999-2018.
Output: portfolio project page + Tableau-ready dashboard data.

## Author
Sridharan (Shri) Gopalsamy Ramaswamy
MPH/MBA, Washington University in St. Louis
Siteman Cancer Center Research Fellow

## Upstream
This project depends on data and analysis outputs produced by the
`nhanes-cancer-survival` project:

- Source data: `../nhanes-cancer-survival/data/analytic_cohort_cv.csv`
- Source models: `../nhanes-cancer-survival/analysis/cv_risk_gaps/`
  - forest_data.csv
  - cycle_trends_bp_controlled.csv
  - model_*.csv
  - SUMMARY.md

If those upstream outputs change, rerun `scripts/build_assets.py` to regenerate
figures and the Tableau export.

## Key Variables Used
- cancer (1 = self-report cancer history, MCQ220)
- hypertension, diabetes, obese
- bp_controlled, a1c_controlled, chol_high, on_bp_meds, on_chol_meds
- depressed (PHQ-9 >= 10), phq9_severity
- age, female, race_ethnicity, smoking
- wt_pooled, SDMVPSU, SDMVSTRA

## Headline Numbers
- BP control among hypertensives: cancer OR 1.26 (1.10, 1.44), p = 0.001
- A1c control among diabetics:    cancer OR 1.33 (1.03, 1.72), p = 0.031
- High cholesterol (full sample): cancer OR 0.86 (0.71, 1.04), p = 0.111
- All cancer x depressed interactions p > 0.09 (depression does not modify)

## Visual Style
Dark portfolio theme to match `survival-analysis.html`:
- Background: #0F0D2A (deep indigo)
- Panel:      #1A1540
- Text:       #E0E7FF
- Muted:      #A5B4FC
- Accent:     #818CF8
- Pink:       #F472B6
- Green:      #34D399
- Plus Jakarta Sans, 300 DPI exports.

## Rules
- Python only (matplotlib, pandas, numpy, statsmodels)
- No em dashes in narrative
- No AI-sounding language
- Match the structure and tone of `nhanes-cancer-survival/docs/PROJECT_WALKTHROUGH.md`
