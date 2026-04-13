# I2DB Datathon — Diabetes Risk Prediction

## What this project is
A competition to build a model that predicts whether a diabetes patient's A1c will become **uncontrolled** in the next year, using 12 months of prior EHR data. First prize is $2,000. Deadline: April 6, 2026. Presentation at the I2DB Symposium: April 13.

## The data
Two CSV files in this folder:
- `DM_Features.csv` — 62,425 patients, 41 columns (demographics, A1c labs, medications, cholesterol, utilization, comorbidities, ADI)
- `DM_Control_2025.csv` — Same 62,425 patients, 1 column: `a1c 2025 Uncontrolled` (True/False)

Both files share the same index (patient ID). This is a **binary classification** problem. The classes are imbalanced: 89.4% controlled (False), 10.6% uncontrolled (True).

### Key data facts
- `a1c 1-estimated result` is 100% complete. Later A1c columns get progressively sparser (A1c 2: 42%, A1c 3: 12%, A1c 4-5: 2.8%)
- Weight/height: ~73% missing. Insurance: 67% missing. ADI: 37-48% missing
- Medications and utilization columns have zero missingness (zeros mean zero)
- **LEAKAGE WARNING**: The column `a1c 2025-collection date-time-days from reference` is suspect — 100% of patients missing this value are labeled Controlled. Do NOT use this column as a feature without explicit discussion first
- ADI columns are stored as strings in some rows (contain decimals like "10.0") — convert to numeric

## Feature engineering plan
Build features in rounds. See `feature_engineering_plan.xlsx` for the full table with 29 features.

**HIGH priority (build first):**
1. `age` = 2025 - birth year
2. `a1c_latest` = last non-missing A1c value
3. `a1c_change` = last A1c minus first A1c (patients with 2+ readings only)
4. `n_a1c_tests` = count of non-missing A1c values (1-5)
5. `a1c_mean` = mean of all available A1c values
6. `total_med_classes` = count of medication types with orders > 0

**MEDIUM priority (add second):**
- `a1c_max`, `a1c_variability`, `a1c_above_9`, `total_med_orders`, `on_insulin`, `on_newer_drugs`, `no_medication`, `bmi`, `has_bmi`, `total_encounters`, `any_admission`, `any_comorbidity`, `undertreated`, `treatment_resistant`

## Step-by-step workflow
We are following this sequence — do not skip ahead:

1. ~~**Load and look** — read CSVs, check shapes, peek at rows~~ DONE
2. ~~**Understand the target** — class balance, visualize the split~~ DONE
3. ~~**Explore features by group** — distributions, means by outcome, histograms~~ DONE
4. ~~**Map missingness** — heatmap, check if missingness differs by outcome~~ DONE
5. ~~**Check correlations** — correlation matrix, identify redundant features~~ DONE
6. ~~**Clean data** — drop leakage column, fix data types, encode categoricals~~ DONE
7. ~~**Engineer features** — HIGH priority first, then MEDIUM, then test LOW~~ DONE
8. ~~**Train-test split** — 80/20 stratified split, set random_state=42~~ DONE
9. ~~**Baseline model** — logistic regression on HIGH features only~~ DONE (AUC=0.827)
10. ~~**Advanced models** — random forest, XGBoost with defaults~~ DONE (RF AUC=0.847, XGB AUC=0.827)
11. ~~**Tune best model** — GridSearchCV or RandomizedSearchCV~~ DONE (XGBoost tuned AUC=0.852)
12. ~~**Evaluate on test set** — AUC-ROC, confusion matrix, precision-recall, calibration~~ DONE (AUC=0.852, NPV=97%)
13. ~~**Feature importance** — SHAP or built-in importance, connect to clinical reasoning~~ DONE
14. ~~**Subgroup analysis** — AUC by race, gender, age, insurance, ADI~~ DONE (no major disparities)
15. ~~**Generate submission CSV**~~ DONE
16. ~~**Build presentation**~~ DONE

## How I work
- I'm learning ML through this project. I have a clinical/public health background, not CS
- After running code, **briefly explain what the output means** in plain language
- Use clinical analogies when explaining ML concepts
- When showing plots or results, tell me what to look for and why it matters
- Don't rush — I want to understand each step before moving to the next
- If something looks off in the data, flag it and explain the clinical implication

## Tech stack
- Python 3
- pandas, numpy, matplotlib, seaborn for exploration
- scikit-learn for modeling (LogisticRegression, RandomForestClassifier, GridSearchCV)
- xgboost for XGBoost
- Install packages as needed with pip

## Visualizations
- Save all plots as PNG files in the `plots/` folder using plt.savefig() with dpi=150 and bbox_inches='tight'
- Use descriptive file names like `step2_class_balance.png`, `step3_a1c_distribution.png`
- After saving a plot, tell me what to look for in it and what it means clinically
- Create the `plots/` folder if it doesn't exist
- For publication-quality plots, use seaborn with the "whitegrid" style. Use color palettes similar to ggplot2.

## Auto-maintenance
- After completing each step, update `README.md` with what was done, key findings, and any decisions made
- After completing each step, update the CLAUDE.md workflow section to mark the completed step and set the next step as CURRENT STEP
- After completing each step, update the project structure section in CLAUDE.md if new files or folders were created
- Do these updates automatically without me asking

## Project structure
```
datathon/
├── CLAUDE.md              (this file)
├── README.md              (project reference log)
├── DM_Features.csv        (features dataset)
├── DM_Control_2025.csv    (target variable)
├── feature_engineering_plan.xlsx  (reference for all 29 features)
├── exploration.py         (data exploration — Steps 1-5)
├── clean_data.py          (Step 6 — data cleaning script)
├── feature_engineering.py (Step 7 — builds 20 engineered features)
├── DM_Features_cleaned.csv (cleaned features — 62,425 x 36)
├── DM_Features_engineered.csv (engineered features — 62,425 x 56)
├── split_data.py          (Step 8 — train-test split)
├── X_train.csv, X_test.csv, y_train.csv, y_test.csv  (split data)
├── xgb_tuned_model.pkl    (best model — tuned XGBoost)
├── submission.csv         (competition submission — True/False predictions)
├── submission_detailed.csv (predictions + probabilities + actuals)
├── PRESENTATION_OUTLINE.md (13-slide outline with talking points + Q&A)
├── plots/                 (saved visualizations)
└── modeling.py            (model building — later)
```
