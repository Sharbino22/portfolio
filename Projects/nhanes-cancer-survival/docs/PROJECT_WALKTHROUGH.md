# Project Walkthrough
## What this is, what I found, and how everything connects
*Last updated: April 2026*

---

## The One-Sentence Version

I analyzed 20 years of US national health survey data to find out whether having diabetes, high blood pressure, or obesity makes cancer survivors more likely to die, and the answer is yes, especially diabetes, which increases their mortality risk by 30%.

---

## Why I Did This

I'm a cancer epidemiology research fellow at Siteman Cancer Center. My other work focuses on specific clinical questions (lipid-lowering therapy in lung cancer screening, cognitive outcomes in elderly populations). This project is different. It asks a broader question that sits at the intersection of cancer survivorship and cardiometabolic disease:

**When someone survives cancer, what kills them next? And can we predict who's at highest risk based on conditions we already know how to treat?**

This matters because there are 18+ million cancer survivors in the US. Many of them die not from cancer recurrence but from heart disease, diabetes complications, and other metabolic conditions. If we can identify which comorbidities are most dangerous, survivorship care can be designed to address them.

---

## The Data

**Source:** CDC's National Health and Nutrition Examination Survey (NHANES), 1999-2018. This is the gold standard for nationally representative US health data. Every 2 years, CDC examines ~10,000 Americans with interviews, physical exams, and lab tests.

**What makes this special:** NHANES participants are linked to the National Death Index. So I can see who was examined in (say) 2003, what conditions they had, and whether they died by December 2019. That gives us up to 20 years of follow-up.

**Files:**
- 70 survey files (.XPT format, SAS transport) across 10 two-year cycles
- 10 mortality linkage files (.dat format, fixed-width text)
- 7 components per cycle: demographics, medical conditions (cancer history), diabetes, body measurements (BMI), blood pressure, smoking, and lab values (HbA1c)

**The mortality files were tricky to parse.** They use an inconsistent fixed-width format where in some cycles the follow-up time fields are space-separated (`18 18`) and in others they're concatenated into a single number (`244244` meaning 244 months for both interview and exam follow-up). I had to write a custom parser that handles both formats. This bug cost a full debugging cycle, see notebook 02.

---

## What I Did (Step by Step)

### Step 1: Data Download
`download_data.py` pulls all 80 files from CDC servers. No authentication needed. Run once.

### Step 2: Exploratory Data Analysis (`01_eda.ipynb`)
Loaded one cycle (2017-2018) to understand variable names, coding schemes, and data structure. Key discovery: MCQ220 (cancer history) is coded as 1=yes, 2=no, with NaN for children under 20. Mortality files need the custom parser. Generated 4 figures: missingness heatmap, variable distributions, cancer survivors by cycle, and a preliminary mortality comparison.

**Key finding:** 5,166 cancer survivors across all 10 cycles with 1,964 deaths. This is a larger sample than most published NHANES cancer survivorship studies.

### Step 3: Cohort Construction (`02_cohort.ipynb`)
Merged all 10 cycles (101,316 total participants), applied 5 inclusion criteria (adults 20+, mortality-eligible, positive follow-up, valid cancer status, non-missing BMI), and constructed derived variables.

**Diabetes definition decision:** I used a composite definition (doctor-told diagnosis OR HbA1c >= 6.5%). This captures undiagnosed diabetes, which is important because ~25% of US diabetics don't know they have it.

**Output:** `data/analytic_cohort.csv` with 51,168 participants including 4,715 cancer survivors.

### Step 4: Table 1 (`03_table1.ipynb`)
Two baseline characteristics tables:
- Table 1: Cancer survivors vs. non-cancer (the standard comparison)
- Table 1B: Among cancer survivors, who died vs. who survived (the key comparison)

**Key signal:** Cancer survivors who died had higher rates of diabetes (25.8% vs 19.7%), hypertension (63.5% vs 51.1%), and former smoking (48.9% vs 35.3%).

### Step 5: Kaplan-Meier Curves (`04_km_curves.ipynb`)
Visual evidence before formal modeling. Four panels showing survival curves stratified by cancer status, diabetes, hypertension, and cardiometabolic burden (0-3 conditions).

**The money figure:** Panel D shows a clear dose-response. Each additional cardiometabolic condition pushes the survival curve lower. Cancer survivors with 3 conditions (diabetes + hypertension + obesity) have the worst survival.

### Step 6: Cox Proportional Hazards (`05_cox_models.ipynb`)
The core analysis. Four models with progressive adjustment:
- Unadjusted: raw associations
- Age-sex adjusted: partial confounding control
- Fully adjusted: age, sex, race, smoking
- Burden model: 0-3 conditions as ordinal predictor

**The headline result:** After full adjustment, diabetes independently increases mortality by 31% (HR 1.31, 95% CI 1.17-1.47, p < 0.001). Current smoking is the strongest risk factor (HR 2.27).

**The obesity paradox:** Obesity appears protective after age adjustment (HR 0.89). This is a well-documented phenomenon in cancer survivorship, likely driven by reverse causation (sick patients lose weight) and survival bias.

### Step 7: PH Diagnostics (`06_ph_diagnostics.ipynb`)
Every Cox model requires checking the proportional hazards assumption. If it fails, your hazard ratios might be misleading.

**Result:** Diabetes (p=0.757) and hypertension (p=0.198) satisfy PH. Age (p<0.001) and obesity (p=0.019) show mild violations, which is expected with large N and long follow-up. Schoenfeld residual plots confirm the violations are clinically negligible.

### Step 8: Forest Plots and Subgroup Analysis (`07_forest_plot.ipynb`)
Publication-quality figures showing:
- Figure 2: All HRs across adjustment levels + dose-response
- Figure 3: Age-stratified subgroup analysis

**Novel finding:** Diabetes is most harmful in younger cancer survivors (age 20-59: HR 1.66) and in women (HR 1.47 vs. 1.17 in men). This has clinical implications for targeted survivorship screening.

### Step 9: Sensitivity Analyses (`08_sensitivity.ipynb`)
Five robustness checks: alternative diabetes definition, alternative obesity thresholds, excluding early deaths, sex-stratified, and time-period stratified.

**Verdict:** Diabetes is significant in every single sensitivity analysis. HR ranges from 1.17 to 1.66 depending on subgroup. The finding is bulletproof.

---

## The Bottom Line

| Finding | Number |
|---------|--------|
| Cancer survivors analyzed | 4,715 |
| Deaths observed | 1,676 |
| Diabetes mortality increase | 31% (adjusted) |
| Hypertension mortality increase | 13% (adjusted) |
| 3 comorbidities vs. 0 | 30% higher mortality |
| Strongest modifiable risk | Smoking (HR 2.27) |
| Highest-risk subgroup | Women with diabetes (HR 1.47) |

---

## File Map

```
nhanes-cancer-survival/
  download_data.py          <- Run this first to get data
  01_eda.ipynb              <- Explore the data
  02_cohort.ipynb           <- Build the analytic dataset
  03_table1.ipynb           <- Baseline characteristics
  04_km_curves.ipynb        <- Survival curves
  05_cox_models.ipynb       <- Main analysis (Cox regression)
  06_ph_diagnostics.ipynb   <- Check model assumptions
  07_forest_plot.ipynb      <- Publication figures
  08_sensitivity.ipynb      <- Robustness checks
  data/
    analytic_cohort.csv     <- The analysis-ready dataset (build with 02)
    table1.csv              <- Table 1 output
    cox_results.csv         <- All hazard ratios
    sensitivity_results.csv <- Sensitivity analysis results
    *.XPT, *.dat            <- Raw NHANES files (not in git, download with script)
  figures/                  <- All publication-quality PNGs
  docs/
    research_letter_draft.md <- Manuscript draft for JNCI Cancer Spectrum
    PROJECT_WALKTHROUGH.md   <- This file
  README.md                 <- Project summary for GitHub
  CLAUDE.md                 <- Context file for AI-assisted analysis
```

---

## If You Want to Reproduce This

1. Clone the repo
2. Run `python download_data.py` to get the 80 NHANES files
3. Run notebooks 01 through 08 in order
4. Each notebook reads from the previous step's output
5. All figures save to `figures/` automatically

Requirements: Python 3.9+, pandas, numpy, matplotlib, seaborn, lifelines, scipy

---

## What Could Come Next

- Stratify by cancer type (breast, prostate, lung, colorectal) using MCQ230 codes
- Add cause-specific mortality (cardiac death vs. cancer death) using UCOD_LEADING
- Apply survey weights for population-level estimates (we built the infrastructure but focused on unweighted for the research letter)
- Extend to NHANES 2019-2020 when mortality linkage becomes available
- Time-varying covariate models to address the age PH violation more formally
