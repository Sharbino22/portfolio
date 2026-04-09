# Project: Propensity Score Analysis of Antihypertensive Treatment
**Owner:** Sridharan Gopalsamy Ramaswamy | sridharanshri.com
**Status:** [ ] In Progress | [ ] Complete

---

## Research Question
Does antihypertensive treatment reduce cardiovascular mortality after
adjusting for confounders via propensity scores?

---

## Dataset
| File | Source | Notes |
|------|--------|-------|
| NHANES survey cycles | [wwwn.cdc.gov/nchs/nhanes](https://wwwn.cdc.gov/nchs/nhanes/) | Demographics, exam, lab, questionnaire |
| Linked Mortality Files | [cdc.gov/nchs/data-linkage](https://www.cdc.gov/nchs/data-linkage/mortality.htm) | Follow-up mortality through 2019 |

Same source as the nhanes-survival-analysis project. Download XPT files
from NHANES and the mortality linkage DAT file from NCHS.

---

## Key Variables
- **Treatment:** Self-reported antihypertensive medication use (`BPQ050A`)
- **Outcome:** Cardiovascular mortality (ICD-10 codes I00-I99 in linked mortality)
- **Confounders:** Age, sex, race/ethnicity, BMI, smoking status, diabetes,
  total cholesterol, systolic/diastolic BP, education, income, insurance,
  prior CVD history, eGFR/kidney function
- **Time:** Follow-up in person-months from interview to death or censoring

---

## Methods (in order)
1. Data download and cohort construction (`01_data_prep.ipynb`)
   - Merge NHANES survey + exam + lab + questionnaire + mortality
   - Restrict to adults with hypertension (SBP >= 140, DBP >= 90, or self-reported dx)
   - Define treatment (antihypertensive use) and outcome (CV mortality)
   - Handle missing data, document exclusions
2. Propensity score estimation (`02_propensity_model.ipynb`)
   - Logistic regression: P(treatment | confounders)
   - Covariate balance diagnostics (SMD before/after)
   - Propensity score distribution by treatment group
   - 1:1 nearest-neighbor matching (caliper = 0.2 SD of logit PS)
   - Inverse probability of treatment weighting (IPTW)
   - Trimming extreme weights
3. Matched/weighted outcome analysis (`03_matched_analysis.ipynb`)
   - Kaplan-Meier survival curves: matched and IPTW cohorts
   - Cox proportional hazards: unadjusted, PS-matched, IPTW
   - Sensitivity analysis: subgroup by age, sex, diabetes status
   - Forest plot of treatment effect across subgroups
4. Case study narrative (`04_case_study.ipynb`)
   - Full write-up for HEOR/consulting audience
   - Inline figures, strategic implications, methods transparency

---

## File Map
```
propensity-score-analysis/
  CLAUDE.md               <- You are here. Read this first every session.
  README.md               <- Public-facing project summary
  data/
    raw/                  <- NHANES XPT + mortality DAT files (do not commit)
    processed/            <- Cleaned cohort CSVs from 01_data_prep
  notebooks/
    01_data_prep.ipynb    <- Cohort construction, merge, clean
    02_propensity_model.ipynb <- PS estimation, matching, IPTW, balance
    03_matched_analysis.ipynb <- Survival analysis, Cox models, subgroups
    04_case_study.ipynb   <- Portfolio narrative with inline figures
  figures/                <- All saved PNGs (150 dpi minimum)
  docs/
    case_study.docx       <- Final Word document
```

---

## Critical Rules for Claude Code
- **Never read full CSVs into context.** Use `df.head(10)`, `df.dtypes`, `df.shape` only.
- **Save all key figures** to `/figures/` as PNG at 150 dpi minimum.
- **No debug prints** in final notebook outputs -- clean cells only.
- **Each notebook is self-contained** -- import and load at top of each one.
- **Processed data** (cleaned CSVs) saved to `/data/processed/` by notebook 01,
  used by notebooks 02-04.

---

## Key Findings
- Unadjusted HR of 2.86 attenuates to 1.02-1.24 after PS adjustment, demonstrating massive confounding by indication in observational treatment comparisons
- Method sensitivity: PS matching HR 1.24 (p=0.027), IPTW HR 1.02 (p=0.81), doubly robust HR 1.15 (p=0.09); no single method is definitive
- PH assumption borderline violated (p=0.035 for treatment), suggesting time-varying treatment effect consistent with delayed CV benefit
- Covariate balance achieved: age SMD drops from 0.70 to <0.1 after matching; all covariates below 0.1 threshold
- 3,481 matched pairs from 18,129 hypertensive adults across 20 years of NHANES data

---

## Target Roles This Project Supports
- HEOR consulting (Milliman, Aon, Analysis Group) -- causal inference from observational data
- Life sciences / pharma -- treatment effectiveness, real-world evidence
- Health plan analytics -- risk adjustment, treatment impact modeling
- Academic research -- epidemiologic methods, comparative effectiveness

---

## End-of-Project Checklist
- [x] All 4 notebooks complete and outputs clean
- [x] Figures saved to /figures/ (6 key visuals)
- [x] Key findings documented in this file (above)
- [x] case_study.docx created in /docs/
- [x] Portfolio HTML (index.html) updated with new project card
- [x] README.md finalized
- [x] GitHub repo pushed
- [ ] sridharanshri.com project card live
