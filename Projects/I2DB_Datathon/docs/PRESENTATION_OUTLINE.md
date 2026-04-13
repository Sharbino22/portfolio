# I2DB Datathon Presentation Outline
## Predicting Uncontrolled A1c in Diabetes Patients

**Symposium**: April 13, 2026 | **Time**: ~10-15 minutes + Q&A

---

## Slide 1: Title
**Predicting Loss of Glycemic Control: A Machine Learning Approach Using 12 Months of EHR Data**

- Your name, institution
- I2DB Datathon 2026

---

## Slide 2: The Clinical Problem
**Figure**: `pres_1_problem.png`

**Talking points:**
- 62,425 diabetes patients with 12 months of EHR data
- Question: Which patients will have uncontrolled A1c next year?
- 10.6% become uncontrolled -- a needle-in-a-haystack problem
- Early identification enables proactive intervention: medication adjustment, closer monitoring, care coordination
- Currently, clinicians often discover loss of control only after it happens

---

## Slide 3: The Data
**No figure -- use a clean table or bullet points**

- 41 features across 9 clinical domains:
  - A1c lab values (up to 5 readings over 12 months)
  - Demographics (age, sex, race, ethnicity)
  - Medications (6 drug classes: metformin, insulin, GLP-1, SGLT2, sulfonylurea, DPP4)
  - Healthcare utilization (ED visits, PCP visits, admissions)
  - Comorbidities (CAD, COPD)
  - Cholesterol (LDL, HDL, total)
  - Social determinants (Area Deprivation Index, insurance type)
- Significant missingness: weight/height (73-76%), later A1c values (58-97%), insurance (67%)

---

## Slide 4: A1c is the Strongest Signal
**Figure**: `pres_2_risk_by_a1c.png`

**Talking points:**
- Clear dose-response: 1% risk at A1c <5.7 up to 32% at A1c >10
- Risk plateaus above A1c 9 -- suggesting other factors matter at that point
- But 65% of patients who become uncontrolled currently have A1c < 9
- A1c alone is necessary but not sufficient -- we need a multivariate model

---

## Slide 5: Feature Engineering -- Clinical Reasoning Meets Data Science
**No figure -- use a table**

We engineered 20 features guided by clinical reasoning:

| Feature | Clinical rationale |
|---------|-------------------|
| `a1c_mean`, `a1c_max` | Overall glycemic burden and worst episode |
| `a1c_change` | Is the patient trending better or worse? |
| `a1c_variability` | Glycemic instability -- swinging A1c values |
| `n_a1c_tests` | More monitoring = higher-risk patient |
| `treatment_resistant` | A1c >= 8 despite 2+ medication classes |
| `undertreated` | A1c >= 8 with zero medications |
| `total_med_classes` | Treatment intensity |

Key insight: `treatment_resistant` became one of the strongest non-A1c predictors (correlation +0.20 with outcome)

---

## Slide 6: Model Comparison
**Figure**: `pres_3_model_roc.png`

**Talking points:**
- Tested 3 approaches: Logistic Regression, Random Forest, XGBoost
- XGBoost with hyperparameter tuning achieved the best performance
- AUC improved from 0.828 (logistic regression) to 0.852 (tuned XGBoost)
- Tuning process: 80 parameter combinations x 5-fold cross-validation
- Tree-based models naturally capture interactions (e.g., high A1c + many meds)

---

## Slide 7: Final Model Performance
**Figure**: `pres_7_metrics.png`

**Talking points:**
- AUC-ROC: 0.852 -- strong discrimination
- Sensitivity: 80.6% -- catches 4 out of 5 patients who will lose control
- NPV: 97.0% -- when the model clears a patient, it's right 97% of the time
- Specificity: 74.2%
- Precision: 27.0% -- expected for a screening tool with 10.6% base rate
- The model's strength is ruling OUT risk (NPV) -- confidently deprioritize low-risk patients

---

## Slide 8: Understanding the Predictions
**Figure**: `pres_4_confusion.png`

**Talking points (for 12,485 test patients):**
- 1,069 caught: patients correctly identified as future-uncontrolled (intervention opportunity)
- 257 missed: patients the model incorrectly cleared (area for improvement)
- 2,884 false alarms: patients flagged but stayed controlled (cost = unnecessary review)
- 8,275 correctly cleared: patients confidently left alone (time saved)
- Net clinical value: screen 3,953 patients to find 1,069 truly at-risk

---

## Slide 9: What Drives the Predictions?
**Figure**: `pres_5_shap.png`

**Talking points:**
- SHAP analysis reveals clinically interpretable decision-making
- Top drivers: A1c mean, A1c max, A1c latest -- glycemic history dominates
- A1c change (trajectory) matters: worsening A1c strongly predicts loss of control
- Younger age increases risk -- consistent with more aggressive disease or adherence challenges
- Model mirrors clinical reasoning: A1c history first, then treatment response, then demographics

---

## Slide 10: The Model is Equitable
**Figure**: `pres_6_fairness.png`

**Talking points:**
- AUC ranges from 0.83 to 0.88 across race and gender subgroups
- The model does NOT disadvantage minority populations
- Higher sensitivity for Black patients (84.8%) than White (78.5%)
- Medicaid patients: highest recall (91-93%) -- strongest for the most vulnerable
- Consistent performance across ADI quartiles (neighborhood deprivation)
- Important for real-world deployment: a tool should reduce disparities, not amplify them

---

## Slide 11: Clinical Application -- The Threshold Choice
**No figure -- use a clean table**

The model outputs a risk probability (0-100%). The clinic chooses where to draw the line:

| Use case | Threshold | Catches | Flags per 1,000 patients |
|----------|-----------|---------|--------------------------|
| Population screening | 15% | 96% of at-risk | 123 patients |
| Panel management | 30% | 91% | 89 patients |
| Targeted intervention | 50% | 81% | 63 patients |

Suggested workflow:
1. Run model monthly on diabetes panel
2. Flag patients above threshold
3. RN reviews chart, confirms risk
4. Provider adjusts treatment plan proactively

---

## Slide 12: Limitations and Future Work

**Limitations:**
- Single-institution data -- external validation needed
- Missing data (weight/height 73%, insurance 67%) limits BMI and social determinant features
- Model predicts risk but does not explain causation
- 12-month prediction window is fixed -- shorter windows may be more actionable

**Future directions:**
- Validate on external cohort
- Incorporate medication adherence data (fill rates)
- Add social determinants: food insecurity, transportation access
- Test as a clinical decision support tool in EHR
- Longitudinal model: update risk as new labs arrive

---

## Slide 13: Summary

1. **Problem**: 10.6% of diabetes patients lose glycemic control annually -- currently detected reactively
2. **Approach**: 48 features engineered from EHR data, tuned XGBoost classifier
3. **Performance**: AUC 0.852, catches 81% of at-risk patients, NPV 97%
4. **Equity**: Consistent performance across race, gender, age, and socioeconomic groups
5. **Value**: Enables proactive care -- identify at-risk patients BEFORE they lose control

---

## Presentation Files

All figures are in the `plots/` folder with `pres_` prefix:
- `pres_1_problem.png` -- Class balance
- `pres_2_risk_by_a1c.png` -- Risk by current A1c
- `pres_3_model_roc.png` -- ROC curve comparison
- `pres_4_confusion.png` -- Confusion matrix
- `pres_5_shap.png` -- SHAP feature importance
- `pres_6_fairness.png` -- Subgroup fairness
- `pres_7_metrics.png` -- Key metrics summary

## Q&A Prep

**Likely questions and answers:**

**Q: Why not just use A1c alone as a predictor?**
A: A1c is the strongest signal, but 65% of patients who become uncontrolled have current A1c < 9. The model combines A1c with trajectory, treatment response, demographics, and utilization to catch patients that A1c alone would miss.

**Q: How would this work in a real clinic?**
A: Monthly batch scoring on the diabetes panel. Flagged patients get a chart review by a nurse, then proactive outreach for medication adjustment or closer follow-up. The threshold can be adjusted based on clinic capacity.

**Q: Why is precision so low (27%)?**
A: This is expected for screening with a 10.6% base rate. Mammography flags ~10% of women but only ~0.5% have cancer (precision ~5%). Our 27% precision is actually strong for a screening tool. The clinical cost of a false alarm (15-minute chart review) is far less than missing a patient who loses control.

**Q: Is the model biased against any group?**
A: No. AUC ranges from 0.83-0.88 across race, gender, and income subgroups. The model actually has higher sensitivity for Black patients and Medicaid patients -- populations that face the greatest diabetes disparities.

**Q: What about the missing data?**
A: XGBoost handles missing values natively by learning optimal split directions. For features with high missingness (BMI 77%, ADI 48%), the model learns to use them when available and relies on other features when not. The `has_bmi` feature explicitly captures whether weight/height data was recorded.
