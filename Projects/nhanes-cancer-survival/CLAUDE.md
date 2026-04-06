# NHANES Cancer Survivorship Project — Context File

## Project Goal
Analyze whether cardiometabolic comorbidities (diabetes, hypertension, obesity) are
independently associated with all-cause mortality among US adult cancer survivors.
Target output: research brief/letter suitable for Journal of Cancer Survivorship,
Cancer Epidemiology Biomarkers & Prevention, or JNCI Cancer Spectrum.

## Author
Sridharan (Shri) Gopalsamy Ramaswamy
MPH/MBA, Washington University in St. Louis
Siteman Cancer Center Research Fellow
Portfolio: sridharanshri.com

## Data
All files in data/ folder. Downloaded from CDC, no authentication needed.

**Survey files (70 .XPT):** NHANES cycles 1999-2018, named like:
  2017-2018_demo.XPT, 2017-2018_mcq.XPT, 2017-2018_mortality.dat

**Components per cycle:**
- demo   = DEMO    — age (RIDAGEYR), sex (RIAGENDR), race (RIDRETH1)
- mcq    = MCQ     — cancer history (MCQ220), cancer type (MCQ230A-D)
- diq    = DIQ     — diabetes diagnosis (DIQ010)
- bmx    = BMX     — BMI (BMXBMI)
- bpq    = BPQ     — hypertension (BPQ020)
- smq    = SMQ     — smoking (SMQ020, SMQ040)
- ghb    = GHB/LAB — HbA1c (LBXGH)

**Mortality files (10 .dat):** Fixed-width ASCII, one per cycle, named like:
  2017-2018_mortality.dat
  Columns: SEQN (1-14), ELIGSTAT (15), MORTSTAT (16), UCOD_LEADING (17-19),
           PERMTH_INT (22-24), PERMTH_EXM (25-27)
  MORTSTAT: 0=alive/censored, 1=deceased
  PERMTH_EXM = person-months follow-up from exam date (divide by 12 for years)
  Follow-up through December 31, 2019.

## Key Variables
- Cancer survivor: MCQ220 == 1 (ever told had cancer, excluding non-melanoma skin)
- Diabetes: DIQ010 == 1 (doctor told) OR LBXGH >= 6.5%
- Hypertension: BPQ020 == 1
- Obesity: BMXBMI >= 30
- Smoking: derived from SMQ020 + SMQ040 (Never / Former / Current)
- Outcome: MORTSTAT == 1 (dead), time = PERMTH_EXM / 12

## Inclusion Criteria
- Age >= 20 at NHANES exam
- Eligible for mortality follow-up (ELIGSTAT == 1)
- Positive follow-up time (PERMTH_EXM > 0)

## Analysis Plan (step by step)
- Step 1: Data download         DONE
- Step 2: EDA                   notebook: 01_eda.ipynb
- Step 3: Cohort construction   notebook: 02_cohort.ipynb
- Step 4: Table 1               notebook: 03_table1.ipynb
- Step 5: Kaplan-Meier          notebook: 04_km_curves.ipynb
- Step 6: Cox PH models         notebook: 05_cox_models.ipynb
- Step 7: PH assumption test    notebook: 06_ph_diagnostics.ipynb
- Step 8: Forest plot           notebook: 07_forest_plot.ipynb
- Step 9: Sensitivity analyses  notebook: 08_sensitivity.ipynb
- Step 10: Results + README     narrative + README.md

## Rules
- Python only, Jupyter notebooks (.ipynb)
- No synthetic data
- Publication-quality figures saved to figures/ folder
- No em dashes anywhere in output text
- Libraries: pandas, numpy, matplotlib, seaborn, lifelines, tableone, scipy
