# Propensity Score Analysis of Antihypertensive Treatment

**Author:** Sridharan Gopalsamy Ramaswamy | [sridharanshri.com](https://sridharanshri.com)
**Data:** NHANES 1999-2018 + NCHS Linked Mortality Files (follow-up through Dec 2019)
**Tools:** Python, lifelines, scikit-learn, pandas, matplotlib
**Status:** Complete — 4 notebooks + Word case study

> **About this README.** This is a step-by-step decision log of how the analysis was built, with the actual numbers and the reasoning behind each method choice. If you're skimming, the headline lives in "The one-sentence version" below. If you need to defend or reproduce the work months from now, read the step log.

---

## The one-sentence version

The unadjusted hazard ratio for antihypertensive treatment vs no treatment is **2.86 (treatment looks dramatically harmful)**, but this is entirely confounding by indication: treated patients are systematically older, sicker, and more diabetic than untreated patients. After propensity score adjustment, the HR collapses to **1.02 to 1.24** depending on which method you use — a textbook demonstration of why observational treatment comparisons cannot be trusted without rigorous confounding control.

---

## Why this matters

Comparative effectiveness research and HEOR submissions live or die on whether the analyst can defend that an observational treatment effect is real and not a confounding artifact. This project takes a deliberately messy real-world question (does antihypertensive treatment reduce CV death in NHANES?) and walks through the full propensity score toolkit — matching, IPTW, doubly robust estimation, PH diagnostics, subgroup analysis — to show what it looks like when the methods all (mostly) agree, and what to do when they don't.

The "trick" here is that the dataset has a known confounding pattern: doctors prescribe BP meds *because* patients are sick, so naive analyses make treatment look like it kills people. The whole point of the exercise is to make that artifact disappear and quantify what's left.

---

## Headline numbers

| Model | HR | 95% CI | p | N |
|---|---:|---|---:|---:|
| **Unadjusted** | **2.86** | (2.47, 3.32) | <0.001 | 18,129 |
| **PS-Matched** | **1.24** | (1.02, 1.50) | 0.027 | 6,962 (3,481 pairs) |
| **IPTW** | **1.02** | (0.86, 1.21) | 0.81 | 18,129 |
| **Doubly Robust** | **1.15** | (0.98, 1.36) | 0.09 | 18,129 |

- **Cohort:** 18,129 hypertensive adults from NHANES 1999-2018
- **Treated:** 13,649 (75.3% — note the imbalance, this is *why* PS methods are needed)
- **CV deaths:** 1,641 (9.1%)
- **All-cause deaths:** 4,822 (26.6%)
- **Median follow-up:** 7.8 years
- **Age SMD before adjustment:** 1.02 (huge). **After matching:** 0.008. **After IPTW:** 0.024.

---

## Step-by-step log

### Step 1: Build the mortality file parser (`01_data_prep.ipynb` §1)

- The NCHS Linked Mortality Files are **fixed-width ASCII**, not CSV. Columns are: SEQN (1-14), ELIGSTAT (15), MORTSTAT (16), UCOD_LEADING (17-19), PERMTH_INT (22-24), PERMTH_EXM (25-27)
- Wrote a small parser using `pd.read_fwf` with explicit column specs
- Test load on one cycle: N=6,219, Deaths=1,126
- `MORTSTAT == 1` means deceased; `PERMTH_EXM` is person-months follow-up from exam date (divide by 12 for years)

**Decision:** Reuse the same mortality parser approach as the upstream `nhanes-cancer-survival` project so the two cohorts are comparable. Don't reinvent.

### Step 2: Merge all 10 NHANES cycles (`01_data_prep.ipynb` §2)

- Merged demo + BPQ + BMX + DIQ + SMQ + GHB across 10 cycles (1999-2018)
- After merge: **101,316 person-cycle observations**, 17 columns
- Note this is more than the eventual cohort because we haven't filtered to adults / mortality-eligible / hypertensive yet

**Decision:** Pull all 10 cycles even though some don't have every component. Pre-2005 cycles lack some lab files, but BPQ020 (the hypertension question) is in every cycle, so we don't lose cohort just because PHQ-9 is missing.

### Step 3: Define the cohort (`01_data_prep.ipynb` §3)

The exclusion cascade:

| Filter | Remaining | Dropped |
|---|---:|---:|
| All NHANES participants | 101,316 | — |
| Adults aged 20+ | 55,081 | -46,235 |
| Mortality-eligible (`ELIGSTAT == 1`) | 54,945 | -136 |
| Valid follow-up (`PERMTH_EXM > 0`) | 52,287 | -2,658 |
| **Self-reported hypertension (`BPQ020 == 1`)** | **18,129** | -34,158 |

**Decision:** Define hypertension as self-reported physician diagnosis (`BPQ020`), not as BP-reading-based (SBP ≥ 140 or DBP ≥ 90). Two reasons: (1) the BPX exam files weren't available in the shared data directory at the time; (2) more importantly, the *exposure* of interest is "treated for hypertension," and you can only be treated if you've been told you have it. Using the diagnosis-based definition aligns the cohort with real-world treatment decisions.

**Trade-off:** Misses untreated hypertensives who never got diagnosed. That's a real limitation but it actually strengthens the contrast between the treated and untreated arms — both groups have at least been told they're hypertensive.

### Step 4: Define treatment, outcome, and covariates (`01_data_prep.ipynb` §4)

- **Treatment:** `BPQ050A == 1` (currently taking antihypertensive medication). Yields **13,649 treated (75.3%)** and **4,480 untreated (24.7%)**
- **CV mortality outcome:** UCOD leading cause `001` (heart disease) OR `005` (cerebrovascular disease) from the NCHS 10-leading-causes classification. Yields **1,641 CV deaths (9.1%)**
- **All-cause death** kept as a sanity-check outcome: 4,822 (26.6%)
- **Median follow-up: 7.8 years** (longer is better for survival analyses; we have plenty of events)
- **Covariates** (12 total): age, sex, race/ethnicity (5 dummies), education, poverty-income ratio, BMI, diabetes, smoking, HbA1c

**The 75.3% treated rate is the whole point of using PS methods.** In a balanced (~50/50) trial-style dataset, basic regression would do most of the work. Here the imbalance is severe AND non-random (treated patients are systematically older), so the variance of any unadjusted estimator is dominated by the small untreated group, and the bias is dominated by the systematic age/comorbidity differences.

### Step 5: Handle missing data (`01_data_prep.ipynb` §5)

| Variable | Missing | % |
|---|---:|---:|
| education | 34 | 0.2% |
| pir (poverty-income ratio) | 1,670 | 9.2% |
| bmi | 508 | 2.8% |
| hba1c | 909 | 5.0% |

- **Decision:** Median imputation for all four. Justification: missingness is low (<10% for the worst case), and median imputation preserves the marginal distribution. Multiple imputation would be more rigorous but adds complexity disproportionate to the missingness rate. For a regulatory submission I'd switch to MI; for this portfolio analysis, single imputation is defensible
- After imputation: **N = 18,129, missing = 0**
- Saved to `data/processed/hypertension_cohort.csv` (1.4 MB)

### Step 6: Estimate propensity scores (`02_propensity_model.ipynb` §1)

- **Model:** Logistic regression of `treated` on the 12 covariates (with race one-hot encoded into 4 dummies, dropping the largest reference category)
- **Convergence warnings:** sklearn fired several "divide by zero / overflow / invalid value encountered in matmul" warnings, which is the LBFGS solver complaining about extreme PS values. Refit completed normally; warnings are diagnostic, not failures
- **PS model accuracy: 0.810** — i.e. the covariates predict treatment status with 81% accuracy. That's a *strong* confounding signal: treatment is highly determined by baseline characteristics
- **PS range:** 0.0647 to 0.9946 (full unit interval covered, no extreme zero or one cases)
- **PS median:** treated = 0.866, untreated = 0.585. Big separation, as expected

**Why 0.810 accuracy is informative:** If treatment were assigned randomly (RCT), the PS model would have ~50% accuracy. Our 81% means there is substantial systematic difference between groups — exactly the situation where naive comparisons are dangerous and PS methods help.

### Step 7: 1:1 nearest-neighbor matching with caliper (`02_propensity_model.ipynb` §2)

- Caliper = **0.2 × SD of logit PS = 0.2477** on the logit scale (Austin 2011 default)
- Greedy 1:1 matching without replacement
- **Yield:** 3,481 matched pairs → **6,962 patients** in the matched sample (3,481 treated + 3,481 controls)

**Decision: caliper = 0.2 SD.** This is the convention from Austin's methods papers — wider calipers admit more pairs but worse balance, narrower ones drop too much data. 0.2 hits the standard sweet spot.

**Decision: greedy without replacement.** Optimal matching (Hungarian algorithm) would minimize total imbalance but is computationally expensive on 18K rows and produces only marginal improvements over greedy. Without replacement keeps each control patient in at most one pair (cleaner inference).

**The data loss matters:** We started with 13,649 treated and 4,480 controls and ended with 3,481 pairs. That's only ~25% of the treated arm and ~78% of the control arm. **PS matching trades sample size for balance.** This is the motivation for also doing IPTW in the next step, which keeps everyone.

### Step 8: IPTW weights (`02_propensity_model.ipynb` §3)

- ATE weights: `1/PS` for treated, `1/(1-PS)` for untreated
- **Raw weight range: 1.01 to 103.04** — that's an extreme weight (one untreated patient with PS very close to 1 gets pulled into the analysis with 100x leverage). This will inflate variance enormously
- **Trimmed at the 99th percentile to cap at 15.36**

**Decision: trim at the 99th percentile.** Standard practice in IPTW. Untrimmed weights of 100+ are dominated by single observations and produce noisy, unstable HR estimates. Trimming biases slightly (you're discarding info from extreme PS regions) but the variance reduction is more than worth it.

### Step 9: Covariate balance — Love plot (`02_propensity_model.ipynb` §4)

Standardized mean differences (SMD) before vs after adjustment:

| Covariate | Unadjusted | Matched | IPTW |
|---|---:|---:|---:|
| **age** | **1.020** | **0.008** | 0.025 |
| diabetes | 0.476 | 0.060 | 0.070 |
| hba1c | 0.337 | 0.003 | 0.032 |
| female | 0.126 | 0.017 | 0.015 |
| bmi | 0.102 | 0.006 | 0.047 |
| education | 0.084 | 0.017 | 0.020 |
| pir | 0.075 | 0.012 | 0.005 |
| smoker | 0.060 | 0.005 | 0.004 |

- **Conventional cutoff for "balanced":** SMD < 0.10
- **Both matching and IPTW achieve all SMDs < 0.10**, so the covariate balance is acceptable
- **Age was the dominant confounder** (SMD = 1.02 unadjusted is enormous), and matching essentially eliminated it (SMD = 0.008)
- Love plot saved as `figures/love_plot.png` — the visual that regulators and reviewers actually want to see in CER submissions

### Step 10: Kaplan-Meier curves (`03_matched_analysis.ipynb` §1)

- Two-panel KM: unadjusted full cohort + PS-matched cohort
- **Unadjusted:** dramatic separation, treated patients dying much faster (because they're sicker)
- **Matched:** the curves converge substantially. There's still a small remaining gap, suggesting either residual confounding or a real (small) treatment effect
- Saved as `figures/km_curves.png`

### Step 11: Four Cox PH models — the headline result (`03_matched_analysis.ipynb` §2)

| Model | HR | 95% CI | p | N |
|---|---:|---|---:|---:|
| **Unadjusted** | **2.862** | (2.468, 3.318) | 4.0e-44 | 18,129 |
| **PS-Matched** | **1.240** | (1.025, 1.501) | 0.0269 | 6,962 |
| **IPTW** | **1.021** | (0.865, 1.205) | 0.808 | 18,129 |
| **Doubly Robust** | **1.154** | (0.977, 1.362) | 0.091 | 18,129 |

- **The HR drops from 2.86 to 1.02-1.24** after confounding adjustment. This is the textbook "confounding by indication" demonstration
- **PS matching (HR 1.24)** is borderline significant. Plausible interpretation: treated patients still have slightly worse CV outcomes after accounting for measured confounders, possibly due to unmeasured severity (BP control level, drug class, adherence)
- **IPTW (HR 1.02)** finds essentially no effect. Uses the full cohort but is more sensitive to extreme weights (even after trimming)
- **Doubly robust (HR 1.15)** combines IPTW with covariate adjustment — protects against misspecification of either the PS model OR the outcome model. Lands between matching and IPTW
- Saved as `figures/hr_forest_plot.png`

**Decision: report all four, not just one.** Sensitivity across multiple PS approaches is non-negotiable for HEOR submissions. Presenting a single estimate would be methodologically incomplete. The honest read is: "the effect is somewhere in the 1.0-1.25 range, probably small, possibly null, definitely not the 2.86 disaster the unadjusted model suggests."

### Step 12: Proportional hazards assumption test (`03_matched_analysis.ipynb` §4)

- Lifelines `proportional_hazard_test` on the matched-cohort model
- **Treatment variable: p = 0.0354** — borderline violation. Other covariates pass (age p=0.39, diabetes p=0.32, female p=0.41, smoker p=0.73)
- Visual diagnostic (HR over time, rolling-window) shows the treatment effect appears **larger early in follow-up** and attenuates over time
- Saved as `figures/ph_test_plot.png`

**Why this is plausible:** Antihypertensives reduce CV risk gradually as long-term BP control accrues. The early-follow-up period has a higher hazard ratio because sicker patients start treatment and die before the long-term protection kicks in. This is a *clinically meaningful* PH violation, not a statistical artifact, and it suggests a time-varying coefficient model would be more appropriate for definitive analysis.

**Decision: flag the violation but don't refit with `strata=['treated']`.** Stratifying on treatment would prevent estimating the treatment HR at all, defeating the point. The right next step (for a publication) would be a time-varying-coefficient Cox model, which is outside the scope of this portfolio piece.

### Step 13: Subgroup analysis (`03_matched_analysis.ipynb` §5)

| Subgroup | HR | 95% CI | p | N | Events |
|---|---:|---|---:|---:|---:|
| **Age < 65** | **1.748** | (1.273, 2.398) | **0.0005** | 5,261 | 163 |
| Age ≥ 65 | 0.991 | (0.778, 1.262) | 0.94 | 1,701 | 263 |
| Male | 1.203 | (0.940, 1.540) | 0.14 | 3,472 | 254 |
| Female | 1.294 | (0.958, 1.748) | 0.09 | 3,490 | 172 |
| No diabetes | 1.245 | (1.004, 1.544) | 0.046 | 5,975 | 334 |
| Diabetes | 1.130 | (0.748, 1.707) | 0.56 | 987 | 92 |
| Non-smoker | 1.223 | (0.911, 1.643) | 0.18 | 3,325 | 178 |
| Smoker | 1.252 | (0.975, 1.608) | 0.08 | 3,637 | 248 |

- **Age < 65 is the standout:** HR 1.75, p=0.0005. The matched-cohort treatment effect is concentrated in younger hypertensives. In adults 65+, the HR collapses to 0.99 (no effect)
- The age <65 finding is consistent with the early-follow-up amplification seen in the PH test — younger sicker patients on treatment may be at the front edge of the lag-to-benefit window
- Saved as `figures/subgroup_forest_plot.png`

**Caveat:** Subgroup analyses are exploratory. Multiple comparisons across 4 stratifiers + 2 levels = 8 tests. Without multiplicity correction, the Age <65 finding is suggestive but not confirmatory.

### Step 14: Case study narrative (`04_case_study.ipynb`)

- Executive summary, six analysis sections, each with embedded figures and a "Takeaway" callout
- Strategic implications table mapping methodological findings to HEOR/CER practice
- Methods documentation
- Audience: HEOR consultants and CER analysts

**Decision:** Frame the whole writeup around the *methodological* story (confounding control + sensitivity across methods), not the clinical claim about antihypertensives. The clinical question isn't really resolved by this analysis — what *is* resolved is that you cannot trust unadjusted observational comparisons, and you must report sensitivity across multiple PS methods. That's the transferable lesson.

---

## Strategic implications (the case study payoff)

| Finding | Implication for HEOR / CER practice |
|---|---|
| Unadjusted HR 2.86 reverses after PS adjustment | Observational claims data analyses **require** rigorous confounding control; unadjusted comparisons are unreliable for formulary or coverage decisions |
| HR varies from 1.02 to 1.24 across PS methods | Sensitivity analysis across multiple approaches is **non-negotiable** for HEOR submissions |
| PH assumption borderline violated (p=0.035) | Time-varying treatment effects should be explored; standard Cox models can mask delayed benefit |
| 3,481 matched pairs from 18,129 | Matching discards substantial data; IPTW preserves the full sample and may be preferable when overlap is limited |
| Self-reported treatment is a limitation | Claims-based treatment identification (NDC codes, pharmacy fills) would strengthen a real-world version of this analysis |

---

## Figures (6 total)

| File | Description |
|---|---|
| `ps_distribution.png` | Propensity score distribution by treatment group (overlap diagnostic) |
| `love_plot.png` | Covariate balance: SMDs before vs after matching and IPTW |
| `km_curves.png` | KM survival curves: unadjusted (full cohort) and PS-matched |
| `hr_forest_plot.png` | HR comparison across 4 PS methods (the headline figure) |
| `ph_test_plot.png` | Treatment HR over time (PH assumption assessment) |
| `subgroup_forest_plot.png` | Subgroup HRs by age, sex, diabetes, smoking |

---

## Project structure

```
propensity-score-analysis/
  README.md                      <- This file (step-by-step log)
  CLAUDE.md                      <- AI assistant context
  data/
    raw/                         <- NHANES XPT + mortality DAT files (not committed)
    processed/
      hypertension_cohort.csv    (1.4 MB)
      matched_cohort.csv         (1.0 MB)
      iptw_cohort.csv            (3.2 MB)
  notebooks/
    01_data_prep.ipynb           <- Cohort construction, treatment + outcome definitions, imputation
    02_propensity_model.ipynb    <- PS estimation, matching, IPTW, balance diagnostics
    03_matched_analysis.ipynb    <- Cox models, KM, PH test, subgroups
    04_case_study.ipynb          <- Portfolio narrative with inline figures
  figures/                       <- 6 PNGs at 150 dpi
  docs/
    case_study.docx              <- Final Word document
```

---

## Limitations

1. **Self-reported treatment.** `BPQ050A` captures whether the patient *says* they're taking BP meds — not which drug, what dose, or whether they actually take it. Claims-based treatment identification (NDC codes, pharmacy fill records) would be much stronger for a publication-quality version.
2. **Cross-sectional exposure.** Treatment status is captured at the NHANES exam. Subsequent treatment changes (starting, stopping, switching) are unobserved.
3. **Unmeasured confounders.** PS methods only adjust for *measured* confounders. Things like medication adherence, BP control level, comorbidity severity, prior CV events, and family history are unobserved and could explain the residual HR > 1 in matched analysis.
4. **Borderline PH violation.** The treatment HR is non-constant over follow-up. A time-varying-coefficient Cox model would be more appropriate for definitive estimates.
5. **Single imputation for missing covariates.** Multiple imputation would be more rigorous; single median imputation underestimates SE. Acceptable for a portfolio piece, not for a regulatory submission.
6. **Subgroup analyses are exploratory.** 8 subgroup tests without multiplicity correction.
7. **The "treatment effect" estimated here is not interpretable as causal in a strict sense** — just because we balanced measured confounders doesn't mean we balanced unmeasured ones.

---

## What I'd do differently next time

- Pull NHANES BPX exam data and use the BP-reading-based hypertension definition as a sensitivity check
- Use multiple imputation instead of single median imputation
- Refit the matched Cox model with a time-varying treatment coefficient
- Add an instrumental variable analysis (e.g. provider prescribing rate as instrument) as a third triangulation
- Pre-register the subgroup hypotheses and apply multiplicity correction
- Compare to a published RCT meta-analysis estimate to anchor the magnitude

---

## Relevance

This project demonstrates:
- Propensity score matching, IPTW, and doubly robust estimation **from scratch** (no PSMatch / MatchIt black-box wrappers)
- Comparative effectiveness research (CER) workflow end-to-end
- Cox proportional hazards with formal PH diagnostics
- Sensitivity analysis across multiple causal-inference approaches as a single coherent narrative
- Translation of epidemiologic methods into HEOR-ready deliverables

Directly relevant to:
- **HEOR consulting** (Milliman, Aon, Analysis Group, Genesis Research) — causal inference from observational data, regulatory submissions
- **Life sciences / pharma** — comparative effectiveness, real-world evidence for label expansion
- **Health plan analytics** — risk adjustment, treatment-effect modeling
- **Academic research** — epidemiologic methods, observational study design

---

*Sridharan Gopalsamy Ramaswamy | MPH/MBA, Washington University in St. Louis*
