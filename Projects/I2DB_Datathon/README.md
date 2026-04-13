# I2DB Datathon -- Diabetes Risk Prediction

Predicting whether a diabetes patient's A1c will become uncontrolled in the next year using 12 months of prior EHR data.

## Competition Details

| Item | Detail |
|------|--------|
| Prize | $2,000 (first place) |
| Submission deadline | April 6, 2026 |
| Symposium presentation | April 13, 2026 |
| Task | Binary classification -- predict `a1c 2025 Uncontrolled` (True/False) |

## Dataset Summary

- **Patients**: 62,425
- **Features**: 41 columns (demographics, A1c labs, medications, cholesterol, utilization, comorbidities, ADI)
- **Target**: `a1c 2025 Uncontrolled` -- 10.6% True (uncontrolled), 89.4% False (controlled)
- **Source files**: `DM_Features.csv`, `DM_Control_2025.csv`

## Progress Log

- [x] Step 1: Load and look
- [x] Step 2: Understand the target
- [x] Step 3: Explore features by group
- [x] Step 4: Map missingness
- [x] Step 5: Check correlations
- [x] Step 6: Clean data
- [x] Step 7: Engineer features
- [x] Step 8: Train-test split
- [x] Step 9: Baseline model
- [x] Step 10: Advanced models
- [x] Step 11: Tune best model
- [x] Step 12: Evaluate on test set
- [x] Step 13: Feature importance
- [x] Step 14: Subgroup analysis
- [x] Step 15: Generate submission CSV
- [x] Step 16: Build presentation

## Key Decisions

_(Recorded as we go)_

## Important Findings

### Step 1: Load and look (2026-03-23)
- Both files: 62,425 patients, IDs match perfectly between features and target
- 41 feature columns fall into 9 groups: demographics (4), comorbidities (2), A1c labs (11), weight/height (6), cholesterol (6), utilization (3), insurance (1), medications (6), ADI (2)
- 14 columns have zero missingness (medications, utilization, comorbidities, demographics mostly)
- Heaviest missingness: A1c 4-5 (97%), height (76%), weight (73%), insurance (67%), A1c 2 (58%)
- ADI columns stored as strings -- need numeric conversion
- `a1c 2025-collection date-time-days from reference` flagged as leakage risk

### Step 2: Understand the target (2026-03-23)
- Class imbalance: 89.4% controlled vs 10.6% uncontrolled (roughly 1:8 ratio)
- Uncontrolled patients have higher current A1c: mean 8.78 vs 6.92
- Risk rises steeply with current A1c: 1% (<5.7) -> 6.5% (6.5-7) -> 28% (8-9) -> 32% (>10)
- Risk plateaus around A1c 9-10 (~32%) -- patients above 10 don't have much higher risk than 9-10
- 35.5% of uncontrolled patients currently have A1c >= 9 vs only 9% of controlled
- Current A1c will be the single strongest predictor, but 65% of future-uncontrolled patients have A1c < 9 now, so we need other features too
- Plots: `step2_class_balance.png`, `step2_a1c1_by_outcome.png`, `step2_uncontrolled_rate_by_a1c_bin.png`

### Step 3: Explore features by group (2026-03-23)
**Demographics:**
- Younger patients (<30) have highest uncontrolled rate (14.3%); rate drops with age to 8.8% for 80+
- Males 11.8% uncontrolled vs females 9.6%
- Race disparities: Pacific Islander (15.4%) and American Indian (14.9%) highest; White (10.1%) and Asian (10.2%) lowest
- Hispanic patients 12.8% vs non-Hispanic 10.6%

**Comorbidities:**
- CAD and COPD show flat or slightly increasing uncontrolled rates -- weak signal
- Having any comorbidity doesn't strongly predict uncontrolled A1c

**Medications (strong signal):**
- Uncontrolled patients use more meds across the board: insulin (+12pp), metformin (+11pp), sulfonylurea (+11pp)
- Patients on 4+ med classes have 20-37% uncontrolled rate vs 8.4% for those on zero meds
- This is confounding: sicker patients get more meds AND are harder to control

**Utilization:**
- ED visits show dose-response: 0 visits=9.7%, 5+=18.4%
- PCP visits and admissions show minimal difference between groups

**Cholesterol & ADI:**
- LDL, HDL, total cholesterol nearly identical between groups -- weak signal
- ADI national rank nearly identical (64.9 vs 66.0) -- weak signal

**Strongest feature groups so far:** A1c values >> medications > demographics > ED visits >> cholesterol/ADI
- Plots: `step3_demographics.png`, `step3_comorbidities_meds.png`, `step3_util_chol_adi.png`

### Step 4: Map missingness (2026-03-24)
- Missingness is NOT random -- it differs by outcome for several columns
- **LEAKAGE CONFIRMED**: `a1c 2025 (date)` is 0% missing for uncontrolled, 47.7% missing for controlled. If missing -> 100% controlled. Must drop this column.
- A1c 2 is 18.8pp less missing in uncontrolled group (40.9% vs 59.7%) -- uncontrolled patients had more A1c tests
- A1c 3 is 12.8pp less missing in uncontrolled group (76.3% vs 89.1%) -- same pattern
- Cholesterol 5.1pp less missing in uncontrolled group -- they got more labs overall
- Weight/height, insurance, ADI missingness is similar between groups
- **Key insight**: missingness itself is informative -- `n_a1c_tests` (count of non-missing A1c values) will be a useful engineered feature because more monitoring = higher risk patients
- Plots: `step4_missingness_heatmap.png`, `step4_missingness_by_outcome.png`

### Step 5: Check correlations (2026-03-24)
**Correlations with target (uncontrolled):**
- A1c values dominate: a1c_5 (+0.43), a1c_4 (+0.40), a1c_3 (+0.39), a1c_2 (+0.39), a1c_1 (+0.31)
- Medications moderate: sulfonylurea (+0.11), insulin (+0.08), metformin (+0.07)
- Everything else is weak (<0.05): ED visits, cholesterol, ADI, comorbidities

**Redundant feature pairs (|r| > 0.5):**
- ADI state vs national: r=0.96 -- keep only one (national is more generalizable)
- LDL/HDL/total cholesterol: r=0.73-0.77 -- highly redundant, keep total_chol or engineer a ratio
- PCP visits vs admissions: r=0.73 -- combine into total_encounters
- A1c readings are correlated with each other (r=0.52-0.64) -- expected, will aggregate into engineered features (mean, max, change) rather than using raw columns

**Decisions:** Drop ADI state rank (keep national). Aggregate cholesterol into single feature or ratio. Aggregate A1c into summary stats rather than 5 raw columns.
- Plots: `step5_correlation_matrix.png`, `step5_target_correlations.png`

### Step 6: Clean data (2026-03-24)
Went from 41 raw columns to 36 cleaned numeric columns:
- **Dropped**: leakage column, 10 date/timing columns, 2 unit columns, ADI state rank (14 cols removed)
- **Encoded**: gender -> is_male, ethnicity -> is_hispanic, race -> 7 one-hot columns, insurance -> 4 simplified one-hot columns (9 new cols)
- **Fixed**: ADI national rank converted from string to float
- **Insurance simplification**: 12 raw categories -> 4 groups (Medicare, Medicaid, Managed Care, Other)
- **Weight units confirmed all kg, height all cm** -- safe to use directly for BMI later
- Saved as `DM_Features_cleaned.csv`

### Step 7: Engineer features (2026-03-24)
Built 20 new features (6 HIGH + 14 MEDIUM priority). Final dataset: 62,425 x 56 columns.

**Top engineered features by correlation with target:**
- a1c_max (+0.35), a1c_mean (+0.33), a1c_latest (+0.31) -- A1c summaries dominate as expected
- a1c_above_9 (+0.25), a1c_variability (+0.21) -- instability signals are strong
- treatment_resistant (+0.20) -- our confounding-aware feature works well! High A1c despite 2+ meds
- total_med_classes (+0.15), n_a1c_tests (+0.14) -- monitoring intensity captures risk
- undertreated (+0.13) -- high A1c with no meds
- no_medication (-0.12) -- being on no meds = lower risk (these are mild patients)
- BMI, has_bmi, any_admission, any_comorbidity -- all weak individually

**Key insight**: treatment_resistant (+0.20) is one of the strongest non-A1c features, confirming our confounding hypothesis from Step 3. It captures patients who are hard to control despite pharmacologic intervention.

**n_a1c_tests distribution**: 58% have only 1 test, 30% have 2, 9% have 3, 3% have 4-5. More tests = being monitored more closely.

**BMI**: Only 23.5% of patients have both weight+height. Mean BMI = 32.6 (obese range). We keep has_bmi as a separate feature since missingness may be informative.

Saved as `DM_Features_engineered.csv`

### Step 8: Train-test split (2026-03-24)
- 80/20 stratified split with random_state=42
- Train: 49,940 patients (44,634 controlled + 5,306 uncontrolled)
- Test: 12,485 patients (11,159 controlled + 1,326 uncontrolled)
- Class balance preserved exactly: 10.62% uncontrolled in both sets
- Dropped 8 raw columns replaced by engineered features (5 raw A1c, birth year, weight, height)
- Final feature matrix: 48 columns, 39 with zero missing
- 9 columns with missing values -- will be handled by model (tree models handle NaN natively) or imputation

### Step 9: Baseline model (2026-03-24)
**Logistic regression with class_weight='balanced', median imputation, standard scaling**

| Model | AUC-ROC | PR-AUC | Recall (Uncontrolled) | Precision (Uncontrolled) |
|-------|---------|--------|----------------------|------------------------|
| HIGH features only (6) | 0.8267 | 0.3120 | 72% | 28% |
| ALL features (48) | 0.8275 | 0.3216 | 75% | 28% |
| Dummy (always Controlled) | 0.5000 | -- | 0% | -- |

**Key findings:**
- AUC of 0.83 is a strong baseline -- logistic regression already does well with A1c features
- Adding 42 more features barely improves AUC (+0.001) -- the A1c features carry almost all the signal in a linear model
- Recall ~72-75%: catches 3 out of 4 uncontrolled patients
- Precision ~28%: for every patient flagged, only 1 in 4 is truly uncontrolled (lots of false alarms)
- The PR-AUC (0.31-0.32) is ~3x better than random (0.106 baseline) but still low -- this is where tree models should help
- Top coefficients: a1c_mean (+0.94), n_a1c_tests (+0.30), a1c_latest (+0.25), total_med_classes (+0.19)
- Accuracy dropped from 89.4% (dummy) to 77% -- we traded accuracy for recall, which is the right trade in screening

**Decision**: class_weight='balanced' is the right approach -- prioritize finding uncontrolled patients over overall accuracy

### Step 10: Advanced models (2026-03-24)

| Model | AUC-ROC | PR-AUC | Recall | Precision |
|-------|---------|--------|--------|-----------|
| Logistic Regression | 0.8275 | 0.3216 | 75.0% | 27.7% |
| **Random Forest** | **0.8467** | **0.3923** | 68.9% | 31.5% |
| XGBoost (defaults) | 0.8267 | 0.3596 | 64.8% | 30.4% |

- Random Forest is the clear winner on AUC (+0.02 over LR) and especially PR-AUC (+0.07)
- Random Forest improves precision from 28% to 32% while keeping recall solid at 69%
- XGBoost underperformed with defaults -- needs hyperparameter tuning in Step 11
- XGBoost used raw NaN handling (native), RF used median imputation
- All models used class weighting (balanced / scale_pos_weight)
- **Decision**: Tune XGBoost in Step 11 -- it typically beats RF once optimized

### Step 11: Tune best model (2026-03-24)
RandomizedSearchCV: 80 parameter combinations x 5-fold CV = 400 fits

**Best XGBoost parameters:**
- learning_rate=0.01, n_estimators=800, max_depth=5, min_child_weight=10
- subsample=0.7, colsample_bytree=0.5, gamma=0.3, reg_lambda=1

| Model | AUC-ROC | PR-AUC |
|-------|---------|--------|
| Logistic Regression | 0.8275 | 0.3216 |
| Random Forest | 0.8467 | 0.3923 |
| XGBoost (default) | 0.8267 | 0.3596 |
| **XGBoost (tuned)** | **0.8517** | **0.4162** |

- Tuning improved XGBoost from 0.827 to 0.852 AUC (+0.025) and from 0.360 to 0.416 PR-AUC (+0.056)
- Tuned XGBoost now beats Random Forest on both metrics
- Recall jumped to 81% (catches 1,069 of 1,326 uncontrolled patients) -- best of all models
- Precision at 27% -- more false alarms than RF, but catching 81% vs 69% of uncontrolled
- Key tuning insight: smaller learning rate (0.01 vs 0.1) + more trees (800 vs 500) + regularization (gamma=0.3, subsample=0.7, colsample=0.5) = much better generalization
- Saved tuned model as `xgb_tuned_model.pkl`

### Step 12: Evaluate on test set (2026-03-24)
**Final metrics (tuned XGBoost, test set, threshold=0.5):**
- AUC-ROC: 0.8517
- PR-AUC: 0.4162
- Brier Score: 0.1592
- Sensitivity: 80.6% (catches 1,069 of 1,326 uncontrolled)
- Specificity: 74.2%
- PPV: 27.0%
- NPV: 97.0% (of patients cleared by the model, 97% truly stay controlled)

**Threshold analysis** -- can adjust depending on clinical use case:
- Threshold 0.15: catches 96.4% but flags 7,697 patients (huge workload)
- Threshold 0.30: catches 90.6%, flags 5,552
- Threshold 0.50 (default): catches 80.6%, flags 3,953
- Lower threshold = more sensitive (good for screening), higher = more specific (good for intervention)

**Calibration**: Model is reasonably well-calibrated for low probabilities (<0.3) but overestimates risk somewhat in the 0.3-0.6 range. Above 0.7, calibration improves again.

**Key insight**: NPV of 97% is the strongest clinical metric -- if the model says a patient is low risk, there's a 97% chance they truly stay controlled. The model is best at ruling OUT risk.

- Plots: `step12_full_evaluation.png`, `step12_probability_distribution.png`

### Step 13: Feature importance (2026-03-24)
Two methods: XGBoost built-in (gain) and SHAP values. They give slightly different rankings because they measure different things.

**Top features by SHAP (average impact on prediction):**
1. a1c_mean (0.73) -- by far the strongest driver
2. a1c_max (0.50) -- worst A1c reading matters a lot
3. a1c_latest (0.22) -- most recent reading
4. a1c_change (0.11) -- trajectory (getting better or worse)
5. age (0.09) -- younger = higher risk
6. bmi (0.08) -- despite 76% missing, still contributes
7. a1c_variability (0.08) -- unstable A1c = higher risk

**SHAP beeswarm key findings:**
- High a1c_mean (red dots, right side) strongly pushes toward uncontrolled -- the single most important clinical signal
- Higher a1c_change (A1c went UP) pushes toward uncontrolled; negative change (improving) is protective
- Younger age (blue dots = low age, right side) increases risk -- confirms demographic finding from Step 3
- Male sex pushes toward uncontrolled
- Black race has a modest positive SHAP contribution -- important for equity discussion in Step 14
- Sulfonylurea use pushes toward uncontrolled -- likely confounded (prescribed to sicker patients)

**Built-in importance highlights a1c_above_9 as #1** because it's a single binary split that creates the biggest information gain. SHAP more accurately captures continuous features like a1c_mean.

**Engineered features that earned their keep:** treatment_resistant (#4 built-in), undertreated (#6), a1c_variability (#7 SHAP), n_a1c_tests (#14)

- Plots: `step13_feature_importance.png`, `step13_shap_summary.png`, `step13_shap_bar.png`

### Step 14: Subgroup analysis (2026-03-24)
Model performs consistently (AUC 0.83-0.90) across all subgroups. No major fairness red flags.

**By race** (AUC gap = 0.033):
- Asian: 0.880, Black: 0.860, White: 0.847
- Model performs BETTER for minority groups, not worse
- Recall: Black 84.8%, Asian 86.7%, White 78.5% -- catches more minority patients
- Small sample sizes for American Indian and Pacific Islander (excluded from AUC due to n<50 in test set)

**By gender** (AUC gap = 0.043):
- Female: 0.872 vs Male: 0.829 -- model works better for women
- Male FPR higher (29.3% vs 22.8%) -- more false alarms for men

**By age** (AUC gap = 0.025):
- Fairly consistent across groups: 0.837-0.861
- Recall higher in younger patients (83-85% for <55 vs 75% for 75+)

**By ADI** (AUC gap = 0.042):
- Least deprived (1-25): AUC 0.881, Most deprived (76-100): AUC 0.846
- Small gap, but model performs slightly better for less deprived areas

**By insurance**:
- All groups above 0.85 AUC
- Medicaid patients: highest recall (91-93%) -- model is especially sensitive for this vulnerable group

**Key message for presentation**: Model does not disadvantage minority or low-income subgroups. If anything, it catches more uncontrolled patients in these groups. However, higher FPR for some groups means more unnecessary follow-ups.

- Plot: `step14_subgroup_analysis.png`

### Step 15: Generate submission CSV (2026-03-24)
- `submission.csv`: matches target format exactly (patient ID index + True/False column)
- `submission_detailed.csv`: includes predicted probability + predicted class + actual class
- Predicted 19,694 patients as uncontrolled (31.5%) vs actual 6,632 (10.6%) -- model over-flags as expected given high-recall threshold
- Probability range: 0.01 to 0.97, median 0.24

### Step 16: Build presentation (2026-03-24)
- Created 7 publication-ready figures (`pres_1` through `pres_7` in plots/)
- Created `PRESENTATION_OUTLINE.md` with 13-slide structure, talking points, and Q&A prep
- Presentation arc: Problem -> Data -> Insight -> Model -> Results -> Fairness -> Clinical Application -> Limitations

## Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project instructions and workflow |
| `DM_Features.csv` | Features dataset (62,425 x 41) |
| `DM_Control_2025.csv` | Target variable |
| `feature_engineering_plan.xlsx` | Reference for all 29 planned features |
| `exploration.py` | Data exploration script (current work) |
| `plots/` | Saved visualizations |
| `README.md` | This file -- project reference log |
