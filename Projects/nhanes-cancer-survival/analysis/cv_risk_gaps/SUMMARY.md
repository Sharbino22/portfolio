# Cardiovascular Risk Gaps in Cancer Survivors

_Analysis of NHANES 1999-2018, restricted to cycles with PHQ-9 (2005-2018) for models including the depressed covariate._

## Methods

- **Source**: `data/analytic_cohort_cv.csv` (n = 51,168)
- **Estimation**: Survey-weighted logistic regression via `statsmodels.GLM(family=Binomial)`
  with weights normalized so effective N matches actual N (pseudo-likelihood).
- **Standard errors**: Cluster-robust, clustered on combined `SDMVSTRA x SDMVPSU` to
  approximate Taylor-series linearization for the NHANES design.
- **Covariates**: age, sex, race/ethnicity, smoking status, obesity, depression (PHQ-9 >= 10),
  with a cancer * depressed interaction.

## Outcome models

| Outcome | Sample | Cancer survivor OR | 95% CI | p |
|---|---|---:|---|---:|
| BP controlled (hypertensives) | n = 11,772 | 1.26 | (1.10, 1.44) | 0.001 |
| A1c controlled (diabetics) | n = 5,194 | 1.33 | (1.03, 1.72) | 0.031 |
| Total cholesterol >= 240 (all) | n = 32,110 | 0.86 | (0.71, 1.04) | 0.111 |

## Cancer x depression interaction

| Outcome | Interaction OR | 95% CI | p |
|---|---:|---|---:|
| BP controlled (hypertensives) | 0.78 | (0.53, 1.16) | 0.223 |
| A1c controlled (diabetics) | 0.62 | (0.35, 1.09) | 0.097 |
| Total cholesterol >= 240 (all) | 1.25 | (0.79, 1.99) | 0.346 |

## Files

- `table1_cancer_vs_noncancer.csv` — survey-weighted baseline characteristics
- `model_bp_controlled.csv` / `model_a1c_controlled.csv` / `model_chol_high.csv` — full coefficient tables
- `cycle_trends_*.csv` — cancer effect ORs by NHANES cycle
- `forest_data.csv` — data behind the forest plot
- `forest_cancer_effect.png` — summary forest plot

## Caveats

- Pseudo-likelihood with cluster-robust SE approximates the survey design but is not
  identical to Taylor-linearized SEs from R's survey package. Point estimates are
  unbiased; SEs are slightly conservative.
- Depression covariate is only available 2005-2018, so models exclude pre-2005 cycles
  (~13,672 rows).
- BP control and A1c control are conditional outcomes (hypertensives and diabetics only),
  which means the cancer effect estimates the gap among those with the underlying disease,
  not in the full population.