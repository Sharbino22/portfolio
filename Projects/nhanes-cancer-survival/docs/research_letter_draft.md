# RESEARCH LETTER DRAFT
## Target: JNCI Cancer Spectrum (Research Letter format)
## Word limit: 1,500 words, 1 table, 2 figures, 15 references

---

# Cardiometabolic Comorbidity Burden and All-Cause Mortality Among US Cancer Survivors: A 20-Year Population-Based Cohort Study

**Sridharan Gopalsamy Ramaswamy, MPH, MBA**

Division of Public Health Sciences, Washington University School of Medicine, St. Louis, MO

**Corresponding author:** Sridharan Gopalsamy Ramaswamy, MPH, MBA; g.sridharan@wustl.edu

---

## Abstract (150 words max)

**Background:** Cancer survivors face elevated mortality from non-cancer causes, yet the independent contribution of cardiometabolic comorbidities to mortality risk in this population remains incompletely characterized across demographic subgroups.

**Methods:** We analyzed 4,715 adult cancer survivors from the National Health and Nutrition Examination Survey (1999-2018) linked with mortality data through December 2019. Cox proportional hazards models estimated hazard ratios (HR) for all-cause mortality associated with diabetes, hypertension, and obesity, adjusting for age, sex, race/ethnicity, and smoking.

**Results:** Over a median follow-up of 9.2 years, 1,676 deaths occurred. Diabetes was independently associated with 31% higher mortality (HR 1.31, 95% CI 1.17-1.47). A graded dose-response was observed: cancer survivors with 3 cardiometabolic conditions had 30% higher mortality than those with none (HR 1.30, 95% CI 1.08-1.57). The diabetes-mortality association was strongest among women (HR 1.47) and younger survivors aged 20-59 (HR 1.66).

**Conclusions:** Cardiometabolic comorbidity management, particularly diabetes, warrants integration into survivorship care.

---

## Introduction

The population of cancer survivors in the United States exceeds 18 million and continues to grow as screening and treatment improve (1). While cancer-directed therapies remain central to survivorship care, cardiovascular disease and metabolic conditions are increasingly recognized as leading causes of non-cancer mortality in this population (2, 3).

Prior studies have examined individual cardiometabolic risk factors among cancer survivors, but few have assessed the cumulative burden of multiple comorbidities or characterized effect modification by age and sex in a nationally representative sample with extended follow-up (4, 5). Understanding these patterns is essential for developing targeted survivorship care guidelines.

We used 20 years of data from the National Health and Nutrition Examination Survey (NHANES), linked with national mortality records, to evaluate whether diabetes, hypertension, and obesity are independently associated with all-cause mortality among cancer survivors, and whether these associations vary by cardiometabolic burden, age, and sex.

## Methods

### Study Population

We pooled data from 10 NHANES cycles (1999-2018) and linked them with the National Center for Health Statistics (NCHS) Linked Mortality Files, providing mortality follow-up through December 31, 2019. NHANES uses a complex, multistage probability sampling design to generate nationally representative estimates of the US civilian noninstitutionalized population.

We included adults aged 20 years or older who were eligible for mortality follow-up, had positive follow-up time, valid cancer status data, and non-missing body mass index (BMI). Cancer survivors were defined as participants who reported being told by a doctor or health professional that they had cancer or a malignancy of any kind (MCQ220), excluding non-melanoma skin cancer, consistent with prior NHANES cancer survivorship studies (6).

### Exposures

Three cardiometabolic comorbidities served as primary exposures: diabetes (self-reported physician diagnosis or glycated hemoglobin [HbA1c] >= 6.5%), hypertension (self-reported physician diagnosis), and obesity (BMI >= 30 kg/m2). A composite cardiometabolic burden score (0-3) was calculated as the sum of these conditions.

### Covariates

Models adjusted for age (continuous), sex, race/ethnicity (Non-Hispanic White [reference], Non-Hispanic Black, Mexican American, Other Hispanic, Other/Multiracial), and smoking status (never [reference], former, current).

### Statistical Analysis

Cox proportional hazards models estimated hazard ratios (HR) and 95% confidence intervals (CI) for all-cause mortality. We fit four model series: (1) unadjusted, (2) age-sex adjusted, (3) fully adjusted, and (4) cardiometabolic burden as an ordinal variable. The proportional hazards assumption was tested using Schoenfeld residuals.

Subgroup analyses stratified by age group (20-59, 60-79, 80+) and sex. Sensitivity analyses included alternative diabetes definitions (HbA1c-only), alternative obesity thresholds (BMI >= 25, >= 35, continuous per 5 kg/m2), exclusion of participants with less than 1 year of follow-up, and time-period stratification (1999-2008 vs. 2009-2018).

Survey weights were divided by 10 for pooled analysis per NCHS guidance. Analyses were conducted in Python 3.9 using the lifelines package.

## Results

The analytic sample included 51,168 adults, of whom 4,715 (9.2%) reported a cancer history. Cancer survivors were older (mean age 65.7 vs. 47.8 years), more likely to have diabetes (21.9% vs. 14.0%), hypertension (55.5% vs. 32.3%), and a history of smoking (55.8% vs. 44.5%) than participants without cancer (all p < 0.001) (**Table 1**).

Over a median follow-up of 9.2 years, 1,676 deaths occurred among cancer survivors (35.5% mortality).

### Comorbidity-Mortality Associations

In fully adjusted models, diabetes was associated with 31% higher all-cause mortality (HR 1.31, 95% CI 1.17-1.47, p < 0.001) and hypertension with 13% higher mortality (HR 1.13, 95% CI 1.02-1.25, p = 0.018). Obesity was inversely associated with mortality (HR 0.89, 95% CI 0.79-0.99, p = 0.037), consistent with the obesity paradox observed in prior cancer survivorship studies (7) (**Figure 1A**).

Current smoking was the strongest predictor of mortality (HR 2.27, 95% CI 1.94-2.66, p < 0.001).

### Dose-Response

A graded association was observed between cardiometabolic burden and mortality. Compared with cancer survivors with no cardiometabolic conditions, those with 1, 2, and 3 conditions had progressively higher mortality risk (HR 1.11, 1.19, and 1.30, respectively; p for trend = 0.005) (**Figure 1B**).

### Effect Modification

The diabetes-mortality association was strongest among younger cancer survivors aged 20-59 (HR 1.66, 95% CI 1.09-2.53) and attenuated but remained significant in older age groups (60-79: HR 1.36; 80+: HR 1.33). Female cancer survivors showed a stronger diabetes-mortality association (HR 1.47, 95% CI 1.24-1.74) than males (HR 1.17, 95% CI 1.00-1.35) (**Figure 2**).

### Sensitivity Analyses

Results were robust to alternative diabetes definitions (HbA1c-only: HR 1.28), exclusion of early deaths (HR 1.30), and time-period stratification (early cycles: HR 1.32; late cycles: HR 1.28).

The proportional hazards assumption was satisfied for diabetes (p = 0.757) and hypertension (p = 0.198).

## Discussion

In this nationally representative cohort of 4,715 cancer survivors followed for up to 20 years, we found that diabetes was independently associated with a 31% increase in all-cause mortality. This association was consistent across multiple sensitivity analyses and showed meaningful effect modification by age and sex.

Three findings merit emphasis. First, the dose-response relationship between cardiometabolic burden and mortality underscores that comorbidity management in survivorship care should address the full metabolic profile, not individual conditions in isolation. Second, the stronger diabetes-mortality association among younger survivors (HR 1.66 for ages 20-59) suggests that earlier comorbidity screening may yield the greatest survival benefit in this subgroup. Third, the sex disparity (HR 1.47 in women vs. 1.17 in men) aligns with emerging evidence of sex-differential metabolic risk in cancer populations (8) and warrants further investigation.

The inverse association between obesity and mortality is consistent with the obesity paradox described in cancer, cardiovascular disease, and chronic kidney disease populations (7, 9). This finding likely reflects reverse causation (cancer-related weight loss) and survival bias rather than a true protective effect of adiposity.

### Limitations

Cancer history was self-reported without registry confirmation. NHANES top-codes age at 80, which may compress associations in the oldest age group. Comorbidity status was measured at a single time point and may not reflect changes during follow-up. We could not distinguish cancer types or stages in this pooled analysis.

### Conclusion

Diabetes, hypertension, and cumulative cardiometabolic burden are independently associated with excess mortality among US cancer survivors. Integration of metabolic screening and management into survivorship care guidelines, particularly for younger and female cancer survivors, may improve long-term outcomes.

---

## References

1. American Cancer Society. Cancer Treatment & Survivorship Facts & Figures 2022-2024. Atlanta: ACS; 2022.
2. Sturgeon KM, et al. A population-based study of cardiovascular disease mortality risk in US cancer patients. Eur Heart J. 2019;40(48):3889-3897.
3. Zaorsky NG, et al. Causes of death among cancer patients. Ann Oncol. 2017;28(2):400-407.
4. Nipp RD, et al. Disparities in cancer outcomes across age, sex, and race/ethnicity among patients with pancreatic cancer. Cancer Med. 2018;7(2):525-535.
5. Sanford NN, et al. Obesity and cancer prognosis. Cancer. 2019;125(24):4455-4463.
6. Hewitt M, Rowland JH, Yancik R. Cancer survivors in the United States: age, health, and disability. J Gerontol A Biol Sci Med Sci. 2003;58(1):82-91.
7. Lennon H, et al. The obesity paradox in cancer: a review. Curr Oncol Rep. 2016;18(9):56.
8. Lam CSP, et al. Sex differences in heart failure. Eur Heart J. 2019;40(47):3859-3868.
9. Park J, et al. Obesity paradox in end-stage kidney disease patients. Prog Cardiovasc Dis. 2014;56(4):415-425.

---

## Figure Legends

**Figure 1.** Cox proportional hazards results for cardiometabolic comorbidities and all-cause mortality among cancer survivors, NHANES 1999-2018 (N = 4,715). (A) Hazard ratios for individual comorbidities across three levels of adjustment. (B) Dose-response by cardiometabolic burden score (0-3 conditions), fully adjusted.

**Figure 2.** Subgroup analysis of the diabetes-mortality association by age group and sex among cancer survivors. All models adjusted for age (within strata), sex (where applicable), race/ethnicity, and smoking.

---

## Submission Checklist

- [ ] Word count: ~1,450 (within 1,500 limit)
- [ ] Abstract: ~148 words (within 150 limit)
- [ ] Tables: 1 (Table 1 baseline characteristics)
- [ ] Figures: 2 (Forest plot + Subgroup forest)
- [ ] References: 9 (within 15 limit)
- [ ] NHANES citation and weight methodology noted
- [ ] IRB: NHANES is publicly available, de-identified; IRB exempt
- [ ] Data availability: NHANES data available at cdc.gov/nchs/nhanes
- [ ] Conflicts of interest: None
- [ ] Funding: None

## EB-1A Relevance

This publication would demonstrate:
- **Original research contribution** to cancer survivorship science
- **Methodological rigor** (Cox regression, sensitivity analyses, PH diagnostics)
- **First-author publication** in an NCI-affiliated journal (JNCI Cancer Spectrum)
- **Nationally representative data** with clinical policy implications
- Combined with ASCO 2026 presentation, establishes a research trajectory in cancer epidemiology
