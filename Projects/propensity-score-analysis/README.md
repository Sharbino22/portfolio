# Propensity Score Analysis of Antihypertensive Treatment

**Author:** Sridharan Gopalsamy Ramaswamy | [sridharanshri.com](https://sridharanshri.com)  
**Data:** NHANES 1999-2018 + NCHS Linked Mortality Files  
**Tools:** Python, lifelines, scikit-learn, pandas, matplotlib

---

## Research Question

Does antihypertensive treatment reduce cardiovascular mortality after adjusting for confounders via propensity scores?

---

## Key Findings

- **Confounding is massive**: Unadjusted HR of 2.86 (treatment appears harmful) collapses to 1.02-1.24 after PS adjustment, a textbook case of confounding by indication
- **Method sensitivity**: PS matching HR 1.24 (p=0.027), IPTW HR 1.02 (p=0.81), doubly robust HR 1.15 (p=0.09); no single method is definitive
- **PH assumption borderline violated** (p=0.035 for treatment), suggesting time-varying treatment effect consistent with delayed CV benefit of BP control
- **Covariate balance achieved**: Age SMD drops from 0.70 to <0.1 after matching; all covariates below conventional 0.1 threshold
- **3,481 matched pairs** from 18,129 hypertensive adults across 20 years of NHANES data

---

## Data

| Source | Description |
|--------|-------------|
| [NHANES 1999-2018](https://wwwn.cdc.gov/nchs/nhanes/) | 10 survey cycles: demographics, exam, lab, questionnaire |
| [NCHS Linked Mortality](https://www.cdc.gov/nchs/data-linkage/mortality.htm) | Follow-up mortality through December 2019 |

Final cohort: 18,129 adults aged 20+ with self-reported hypertension diagnosis.

---

## Methods and Decisions

### 1. Cohort Construction (`01_data_prep.ipynb`)
- Merged 7 NHANES components per cycle (demo, BPQ, BMX, DIQ, SMQ, GHB) + mortality linkage across 10 cycles
- **Hypertension definition**: Self-reported doctor diagnosis (BPQ020=1). Chose this over BP readings because BPX exam files were not available in the shared data directory
- **Treatment**: Self-reported antihypertensive medication use (BPQ050A=1). 75.3% of the cohort is treated, reflecting real-world prescribing patterns
- **CV mortality**: UCOD leading cause codes 001 (heart disease) or 005 (cerebrovascular disease) from NCHS 10 leading causes classification
- **Missing data**: Median imputation for BMI (2.8%), PIR (9.2%), HbA1c (5.0%), education (0.2%)

### 2. Propensity Score Estimation (`02_propensity_model.ipynb`)
- **Model**: Logistic regression on 12 covariates (age, sex, 4 race dummies, education, poverty-income ratio, BMI, diabetes, smoking, HbA1c)
- **Accuracy**: 81%, reflecting strong confounding signal (treated patients are systematically older and sicker)
- **Matching**: 1:1 greedy nearest-neighbor on logit PS, caliper = 0.2 SD. Yielded 3,481 pairs from 13,649 treated + 4,480 untreated
- **IPTW**: ATE weights (1/PS for treated, 1/(1-PS) for untreated), trimmed at 99th percentile to cap extreme weights at 15.4
- **Balance**: Love plot confirms all SMDs < 0.1 after both matching and IPTW

### 3. Outcome Analysis (`03_matched_analysis.ipynb`)
- **Cox PH models**: Unadjusted, PS-matched, IPTW, doubly robust (IPTW + covariate adjustment)
- **KM curves**: Unadjusted and matched, with log-rank tests
- **PH assessment**: Rolling-window HR over time + formal Schoenfeld residual test. Treatment variable borderline violated (p=0.035); HR appears higher early and attenuates over time
- **Subgroup analysis**: By age (<65 / 65+), sex, diabetes status, smoking. Forest plot shows consistent effect direction

### 4. Case Study Narrative (`04_case_study.ipynb`)
- Executive summary with three headline findings
- Six analysis sections with inline figures and "so what" for HEOR audience
- Strategic implications table mapping findings to consulting deliverables
- Methods documentation

### 5. Word Document (`docs/case_study.docx`)
- Generated programmatically via python-docx
- All 6 figures embedded, formatted tables, figure captions

---

## Figures (6 total)

| Figure | Description |
|--------|-------------|
| `ps_distribution.png` | Propensity score distribution by treatment group |
| `love_plot.png` | Covariate balance: SMD before/after matching and IPTW |
| `km_curves.png` | KM survival curves (unadjusted + PS-matched) |
| `hr_forest_plot.png` | HR comparison across 4 PS methods |
| `ph_test_plot.png` | Treatment HR over time (PH assessment) |
| `subgroup_forest_plot.png` | Subgroup forest plot (age, sex, diabetes, smoking) |

---

## Project Structure

```
propensity-score-analysis/
  README.md                   <- This file
  CLAUDE.md                   <- AI assistant context
  data/
    raw/                      <- NHANES XPT + mortality files (not committed)
    processed/                <- Cohort CSVs from 01_data_prep
  notebooks/
    01_data_prep.ipynb        <- Cohort construction from NHANES
    02_propensity_model.ipynb <- PS estimation, matching, IPTW, balance
    03_matched_analysis.ipynb <- Cox models, KM, PH test, subgroups
    04_case_study.ipynb       <- Narrative with inline figures
  figures/                    <- All PNGs at 150 dpi
  docs/
    case_study.docx           <- Final Word document
```

---

## Relevance

This project demonstrates:
- Propensity score matching and IPTW from scratch (no black-box packages)
- Sensitivity analysis across multiple causal inference approaches
- Cox proportional hazards modeling with diagnostics
- Translation of epidemiologic methods into consulting-ready deliverables

Directly relevant to HEOR consulting (Milliman, Aon, Analysis Group), life sciences comparative effectiveness, and health plan analytics.
