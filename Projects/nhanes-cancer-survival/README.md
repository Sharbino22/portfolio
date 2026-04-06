# Cardiometabolic Comorbidities and Mortality Among US Cancer Survivors
## A Population-Based Cohort Study Using NHANES 1999-2018

**Author:** Sridharan (Shri) Gopalsamy Ramaswamy, MPH/MBA  
**Affiliation:** Washington University in St. Louis, Siteman Cancer Center  
**Date:** April 2026

---

## Research Question

Among US adults with a cancer history, are cardiometabolic comorbidities (diabetes, hypertension, obesity) independently associated with all-cause mortality?

## Key Findings

**Diabetes independently increases all-cause mortality risk by 30% among cancer survivors** (HR 1.30, 95% CI 1.16-1.45, p < 0.001) after adjusting for age, sex, race/ethnicity, and smoking. This association is robust across all sensitivity analyses.

| Comorbidity | Adjusted HR (95% CI) | P-value |
|-------------|---------------------|---------|
| Diabetes | 1.31 (1.17-1.47) | < 0.001 |
| Hypertension | 1.13 (1.02-1.25) | 0.018 |
| Obesity (BMI >= 30) | 0.89 (0.79-0.99) | 0.037 |
| Current smoking | 2.27 (1.94-2.66) | < 0.001 |

### Additional Findings

- **Dose-response relationship:** Each additional cardiometabolic condition increases mortality. Cancer survivors with 3 conditions (diabetes + hypertension + obesity) have 30% higher mortality than those with none (HR 1.30, 95% CI 1.08-1.57).
- **Obesity paradox:** Obesity is paradoxically protective after age adjustment, consistent with published cancer survivorship literature.
- **Sex difference:** Diabetes is more harmful in female cancer survivors (HR 1.47) than males (HR 1.17).
- **Age gradient:** Diabetes risk is highest among younger cancer survivors (age 20-59: HR 1.66).

## Data

- **Source:** CDC National Health and Nutrition Examination Survey (NHANES) 1999-2018 linked with NCHS Mortality Files
- **Sample:** 51,168 US adults aged 20+, including 4,715 cancer survivors
- **Deaths:** 7,778 total (1,676 among cancer survivors)
- **Follow-up:** Median 9.2 years (max 20.8 years)

## Methods

- Retrospective cohort study using 10 pooled NHANES cycles
- Cancer defined as self-reported physician diagnosis (MCQ220)
- Diabetes defined as physician diagnosis OR HbA1c >= 6.5%
- Cox proportional hazards regression with progressive adjustment
- Proportional hazards tested via Schoenfeld residuals
- Sensitivity analyses: alternative exposure definitions, excluding early deaths, sex-stratified, time-period stratified

## Figures

| Figure | Description |
|--------|-------------|
| `figures/km_combined_figure1.png` | Kaplan-Meier curves (4 panels) |
| `figures/figure2_forest_publication.png` | Forest plot: comorbidity HRs + dose-response |
| `figures/figure3_subgroup_forest.png` | Age-stratified subgroup analysis |
| `figures/figure4_sensitivity_diabetes.png` | Sensitivity analysis for diabetes |
| `figures/cancer_survivors_by_cycle.png` | Sample size across NHANES cycles |

## Notebooks

| Step | Notebook | Description |
|------|----------|-------------|
| 1 | `download_data.py` | Data download from CDC |
| 2 | `01_eda.ipynb` | Exploratory data analysis |
| 3 | `02_cohort.ipynb` | Cohort construction and variable derivation |
| 4 | `03_table1.ipynb` | Table 1 baseline characteristics |
| 5 | `04_km_curves.ipynb` | Kaplan-Meier survival curves |
| 6 | `05_cox_models.ipynb` | Cox proportional hazards models |
| 7 | `06_ph_diagnostics.ipynb` | Proportional hazards assumption testing |
| 8 | `07_forest_plot.ipynb` | Publication figures and subgroup analysis |
| 9 | `08_sensitivity.ipynb` | Sensitivity analyses |

## Clinical Implications

Cancer survivorship care should integrate cardiometabolic risk management as a core component. Diabetes screening and management may be particularly important for younger cancer survivors and female cancer survivors, where the mortality impact is greatest.

## Limitations

- Self-reported cancer diagnosis (no cancer registry confirmation)
- NHANES top-codes age at 80, compressing the oldest age group
- Cannot distinguish cancer types in pooled analysis
- Age and obesity show mild PH violations (noted in diagnostics)
- Cross-sectional exposure measurement (comorbidity status at baseline only)

## Tools

Python 3.9, pandas, numpy, matplotlib, seaborn, lifelines, scipy
