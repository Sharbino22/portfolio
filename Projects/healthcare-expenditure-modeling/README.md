# Healthcare Expenditure Modeling: Diabetes Cost Burden by Insurance Type

**Author:** Sridharan Gopalsamy Ramaswamy | [sridharanshri.com](https://sridharanshri.com)
**Data:** MEPS Full Year Consolidated 2022 (HC-243), AHRQ
**Tools:** Python, pandas, numpy, statsmodels, matplotlib

---

## Status

**Partial — 2 of 4 planned notebooks complete (data prep + two-part expenditure model).**
The utilization patterns notebook (`03_utilization_patterns.ipynb`) and the case study narrative notebook (`04_case_study.ipynb`) have not been built yet. Findings below come from the two notebooks that exist and the figures already saved to `figures/`.

---

## Research Question

How do healthcare expenditures differ between diabetic and non-diabetic adults in the US, and does insurance type modify the diabetes cost burden?

---

## Headline Findings

- **Diabetes is one of the strongest predictors of having any healthcare spending at all.** In the Part 1 logistic regression on 17,675 adults, the odds ratio for "any spending in 2022" given a diabetes diagnosis is **OR 4.46 (95% CI 3.42-5.81, p < 0.001)** — larger than any demographic or socioeconomic covariate in the model.
- **Among adults who do spend, diabetes raises expected spending by 66%.** The Part 2 Gamma GLM (log link) on the 15,192 spenders gives an exponentiated diabetes coefficient of **1.66 (95% CI 1.41-1.95, p < 0.001)**, meaning diabetics spend ~1.66x what comparable non-diabetics spend conditional on having any spending.
- **Mean total expenditure**: non-diabetic adults $7,477 vs diabetic adults $16,848 — a 2.25x absolute gap.
- **Excess cost varies by insurance type, but the relative diabetes effect does not.** The diabetes × insurance interaction terms are not statistically significant (all p > 0.7), so diabetes raises spending by roughly the same proportion across insurance categories. But because baseline spending differs by insurance, the *absolute* excess cost ranges from $3,079 (uninsured) to $9,443 (Medicaid).

| Insurance | Non-DM mean | DM mean | Excess cost |
|---|---:|---:|---:|
| Medicaid | $6,081 | $15,524 | **$9,443** |
| Private | $7,329 | $15,478 | $8,149 |
| Medicare | $12,324 | $19,959 | $7,635 |
| Other | $5,622 | $12,718 | $7,096 |
| Uninsured | $1,180 | $4,259 | $3,079 |

The Medicaid result is the most policy-relevant: Medicaid programs absorb the largest absolute per-person cost shock from diabetes. Uninsured diabetics spend the least in absolute terms — but this likely reflects access barriers, not lower clinical need.

---

## Data

| Source | Description | N |
|---|---|---:|
| [MEPS HC-243](https://meps.ahrq.gov) | 2022 Full Year Consolidated File, AHRQ | 22,431 persons |

After restricting to adults with non-missing key covariates: **17,675 analytic sample, 15,192 spenders**.

Run `python download_data.py` to fetch the Stata DTA from MEPS automatically.

---

## Methods and Decisions

### 1. Cohort Construction (`01_data_prep.ipynb`)
- Loaded MEPS HC-243 2022 (22,431 persons), restricted to adults
- Defined diabetes via `DIABDX_M18` (self-reported physician diagnosis)
- Built insurance type categorical from the four flags `PRIV22`, `MCARE22`, `MCAID22`, `UNINS22` with hierarchy: Medicare > Medicaid > Private > Other > Uninsured
- Dropped 156 rows with missing education, leaving 17,675 in the analytic sample
- Saved as `data/processed/analytic_sample.csv`

### 2. Two-Part Expenditure Model (`02_expenditure_model.ipynb`)
**Why two-part?** Healthcare spending is zero-inflated — 14% of adults had no expenditures in 2022. A single-equation linear or log-linear model misspecifies the zero mass. The two-part approach treats the outcome as the product of two separate processes:

- **Part 1 — Logistic regression on P(any spending > 0):**
  - N = 17,675, McFadden pseudo R² = 0.222, AIC = 11,192
  - Diabetes OR 4.46, age OR 1.03/yr, female OR 1.76, hispanic OR 0.50, BMI OR 1.02, education OR 1.08/yr
  - The huge diabetes OR is partly mechanical (people with a diabetes diagnosis are by definition engaged with the healthcare system) but the magnitude still dominates every other covariate

- **Part 2 — Gamma GLM with log link on E(spending | spending > 0):**
  - N = 15,192 spenders, AIC = 328,012
  - Diabetes exp(coef) = 1.66, age 1.012/yr, female 1.18, hispanic 0.76
  - Gamma family + log link is the standard choice for skewed positive expenditure data; preserves multiplicative interpretation of coefficients

- **Combined predictions:** Multiply Part 1 probability × Part 2 expected amount to get unconditional expected expenditure per person, then aggregate by diabetes × insurance to produce the cost burden table above

- **Interaction test:** Added `diabetes × insurance_type` interaction terms to the Part 2 model. ΔAIC = -22 (327,989 vs 328,012). Individual interaction p-values all > 0.7 — i.e. the relative diabetes effect is stable across insurance types. The variation in *absolute* excess cost is driven by baseline spending differences, not by a heterogeneous diabetes treatment effect.

---

## Figures (5 total)

| File | Description |
|---|---|
| `figures/expenditure_distribution.png` | Distribution of total expenditures, log scale, with zero spike highlighted |
| `figures/part1_odds_ratios.png` | Forest-style coefficient plot for Part 1 logistic regression |
| `figures/part2_gamma_coefficients.png` | Coefficient plot for Part 2 Gamma GLM |
| `figures/cost_burden_by_insurance.png` | Bar chart of excess cost (DM minus Non-DM) by insurance type |
| `figures/model_diagnostics.png` | Predicted vs actual diagnostics for the combined two-part model |

---

## Project Structure

```
healthcare-expenditure-modeling/
  README.md                          <- This file
  CLAUDE.md                          <- AI assistant context
  download_data.py                   <- Run once to fetch MEPS HC-243
  data/
    raw/                             <- MEPS Stata DTA (not committed)
    processed/
      analytic_sample.csv            <- 17,675 x 37, output of notebook 01
      diabetes_cohort.csv            <- DM-only subset
  notebooks/
    01_data_prep.ipynb               <- Cohort construction, insurance hierarchy, exclusions
    02_expenditure_model.ipynb       <- Two-part model (logistic + Gamma GLM), interaction test
    [03_utilization_patterns.ipynb]  <- NOT BUILT — planned for ER/IP/office visit count models
    [04_case_study.ipynb]            <- NOT BUILT — planned narrative for portfolio
  figures/                           <- 5 PNGs at 150 dpi (see table above)
```

---

## What's Left

Listed roughly in priority order:
1. **`03_utilization_patterns.ipynb`** — negative binomial regression for `OPTOTV22` (office visits), `ERTOT22` (ER visits), `IPDIS22` (inpatient discharges) by diabetes status and insurance. Will probably show that the diabetes excess cost in Medicaid is driven by both higher office visits AND higher inpatient utilization, while in private insurance it's mostly office/Rx.
2. **`04_case_study.ipynb`** — narrative for actuarial / health-plan-analytics audience. Frame: "the same disease produces a 3x range of per-person cost burden depending on which payer is on the hook."
3. **Portfolio HTML page** — currently no `expenditure-modeling.html` exists. Add to the projects grid in `index.html` once the case study is written.

---

## Relevance

This project demonstrates:
- Two-part / hurdle modeling for zero-inflated cost data (the textbook approach in health econometrics)
- MEPS administrative data fluency
- Translating actuarial cost burden into per-payer dollar impact
- Awareness that interaction terms answer "*does* the effect vary" while marginal differences answer "*how much*"

Directly relevant to actuarial analytics (Milliman, Wakely), HEOR cost-burden studies, payer strategy, and Medicaid managed care plans.

---

## Author

**Sridharan Gopalsamy Ramaswamy**
MPH/MBA Candidate, Washington University in St. Louis
[sridharanshri.com](https://sridharanshri.com)
