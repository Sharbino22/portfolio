import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# ── Step 1: Load and look ──────────────────────────────────────────────────────

features = pd.read_csv('data/raw/DM Features.csv', index_col=0)
target = pd.read_csv('data/raw/DM Control_2025.csv', index_col=0)

# --- Shapes ---
print("=" * 60)
print("SHAPES")
print("=" * 60)
print(f"Features: {features.shape[0]:,} patients x {features.shape[1]} columns")
print(f"Target:   {target.shape[0]:,} patients x {target.shape[1]} column")

# --- Patient ID check ---
print("\n" + "=" * 60)
print("PATIENT ID CHECK")
print("=" * 60)
ids_match = features.index.equals(target.index)
shared = features.index.intersection(target.index)
only_features = features.index.difference(target.index)
only_target = target.index.difference(features.index)
print(f"Indices identical (same order): {ids_match}")
print(f"Shared patients:    {len(shared):,}")
print(f"Only in features:   {len(only_features):,}")
print(f"Only in target:     {len(only_target):,}")

# --- First 5 rows of features ---
print("\n" + "=" * 60)
print("FIRST 5 ROWS -- FEATURES")
print("=" * 60)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
print(features.head(5).T.to_string())

# --- First 5 rows of target ---
print("\n" + "=" * 60)
print("FIRST 5 ROWS -- TARGET")
print("=" * 60)
print(target.head(5).to_string())

# --- Class balance ---
print("\n" + "=" * 60)
print("CLASS BALANCE")
print("=" * 60)
y = target['a1c 2025 Uncontrolled']
vc = y.value_counts()
vcp = y.value_counts(normalize=True).round(3)
for label in vc.index:
    print(f"  {str(label):6s}  {vc[label]:>6,}  ({vcp[label]*100:.1f}%)")

# --- Columns grouped by category ---
print("\n" + "=" * 60)
print("COLUMNS GROUPED BY CATEGORY")
print("=" * 60)

demographics = ['date of birth', 'gender at birth', 'ethnicity', 'race - primary']
comorbidities = ['cad-count', 'copd-count']
a1c_labs = [c for c in features.columns if c.startswith('a1c')]
weight_height = [c for c in features.columns if c.startswith(('weight', 'height'))]
cholesterol = [c for c in features.columns if c.startswith(('ldl', 'hdl', 'total cholesterol'))]
utilization = ['ed vist count-count', 'pcp visit count-count', 'admission count-count']
insurance = ['payor first op visit-primary insurance plan']
medications = ['glp-1 orders-count', 'insulin orders-count', 'metformin orders-count',
               'sglt2 orders-count', 'sulfonylurea orders-count', 'dpp4 orders-count']
adi = ['adi-adi state rank', 'adi-adi national rank']

groups = [
    ('Demographics', demographics),
    ('Comorbidities', comorbidities),
    ('A1c Labs', a1c_labs),
    ('Weight / Height', weight_height),
    ('Cholesterol', cholesterol),
    ('Utilization', utilization),
    ('Insurance', insurance),
    ('Medications', medications),
    ('Area Deprivation Index', adi),
]

for name, cols in groups:
    print(f"\n  {name} ({len(cols)} cols):")
    for c in cols:
        print(f"    - {c}")

# --- Data types + flags ---
print("\n" + "=" * 60)
print("DATA TYPES")
print("=" * 60)
for col in features.columns:
    dtype = features[col].dtype
    flag = ""
    if col in ['adi-adi state rank', 'adi-adi national rank']:
        flag = "  ** SHOULD BE NUMERIC (stored as string)"
    elif col == 'a1c 2025-collection date-time-days from reference':
        flag = "  ** LEAKAGE RISK -- do not use without discussion"
    elif col == 'date of birth':
        flag = "  (year integer -- use to compute age)"
    print(f"  {str(dtype):>8s}  {col}{flag}")

# --- Missing values ---
print("\n" + "=" * 60)
print("MISSING VALUES")
print("=" * 60)
missing = features.isnull().sum()
missing_pct = (missing / len(features) * 100).round(1)
miss_df = pd.DataFrame({'n_missing': missing, 'pct_missing': missing_pct})
miss_df = miss_df.sort_values('pct_missing', ascending=False)
for _, row in miss_df.iterrows():
    if row['n_missing'] > 0:
        print(f"  {row['pct_missing']:5.1f}%  ({row['n_missing']:>5,.0f})  {row.name}")
print(f"\n  Columns with zero missingness: {(missing == 0).sum()}")

# ── Step 2: Understand the target ─────────────────────────────────────────────

print("\n\n")
print("=" * 60)
print("STEP 2: UNDERSTAND THE TARGET")
print("=" * 60)

y = target['a1c 2025 Uncontrolled']
df = features.copy()
df['uncontrolled'] = y.astype(int)

# --- Plot 1: Class balance bar chart ---
fig, axes = plt.subplots(1, 2, figsize=(10, 4))

counts = y.value_counts()
colors = ['#2ecc71', '#e74c3c']
labels = ['Controlled\n(False)', 'Uncontrolled\n(True)']

axes[0].bar(labels, [counts[False], counts[True]], color=colors, edgecolor='black', linewidth=0.5)
axes[0].set_ylabel('Number of patients')
axes[0].set_title('Class Distribution (Counts)')
for i, v in enumerate([counts[False], counts[True]]):
    axes[0].text(i, v + 500, f'{v:,}', ha='center', fontweight='bold')

pcts = [counts[False]/len(y)*100, counts[True]/len(y)*100]
axes[1].bar(labels, pcts, color=colors, edgecolor='black', linewidth=0.5)
axes[1].set_ylabel('Percentage of patients')
axes[1].set_title('Class Distribution (Percentages)')
axes[1].set_ylim(0, 100)
for i, v in enumerate(pcts):
    axes[1].text(i, v + 2, f'{v:.1f}%', ha='center', fontweight='bold')

plt.suptitle('Step 2: Target Variable -- A1c Uncontrolled in 2025', fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('plots/step2_class_balance.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: plots/step2_class_balance.png")

# --- Plot 2: A1c 1 (most recent) distribution by outcome ---
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

a1c1 = df['a1c 1-estimated result']

for label, color, name in [(0, '#2ecc71', 'Controlled'), (1, '#e74c3c', 'Uncontrolled')]:
    subset = a1c1[df['uncontrolled'] == label]
    axes[0].hist(subset, bins=50, alpha=0.6, color=color, label=name, edgecolor='black', linewidth=0.3)

axes[0].set_xlabel('A1c value')
axes[0].set_ylabel('Number of patients')
axes[0].set_title('Distribution of Most Recent A1c by Outcome')
axes[0].legend()
axes[0].axvline(x=9, color='black', linestyle='--', linewidth=1, label='A1c = 9 (clinical threshold)')
axes[0].text(9.2, axes[0].get_ylim()[1]*0.9, 'A1c = 9', fontsize=8)

# Box plot
data_box = [a1c1[df['uncontrolled'] == 0].dropna(), a1c1[df['uncontrolled'] == 1].dropna()]
bp = axes[1].boxplot(data_box, labels=['Controlled', 'Uncontrolled'], patch_artist=True,
                     medianprops=dict(color='black', linewidth=2))
bp['boxes'][0].set_facecolor('#2ecc71')
bp['boxes'][1].set_facecolor('#e74c3c')
axes[1].set_ylabel('A1c value')
axes[1].set_title('A1c 1 (Most Recent) by Outcome')

plt.suptitle('Step 2: A1c Distribution Split by Future Outcome', fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('plots/step2_a1c1_by_outcome.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: plots/step2_a1c1_by_outcome.png")

# --- Stats by outcome ---
print("\n--- A1c 1 (most recent) stats by outcome ---")
grouped = df.groupby('uncontrolled')['a1c 1-estimated result']
stats = grouped.agg(['count', 'mean', 'median', 'std', 'min', 'max'])
stats.index = ['Controlled', 'Uncontrolled']
print(stats.round(2).to_string())

# --- What % of each group has A1c >= 9? ---
print("\n--- Patients with A1c >= 9 (poorly controlled) ---")
for label, name in [(0, 'Controlled'), (1, 'Uncontrolled')]:
    subset = a1c1[df['uncontrolled'] == label]
    n_high = (subset >= 9).sum()
    pct_high = n_high / len(subset) * 100
    print(f"  {name}: {n_high:,} / {len(subset):,} ({pct_high:.1f}%)")

# --- Plot 3: Rate of uncontrolled by A1c 1 bins ---
fig, ax = plt.subplots(figsize=(10, 5))
df['a1c_bin'] = pd.cut(df['a1c 1-estimated result'], bins=[0, 5.7, 6.5, 7, 8, 9, 10, 25],
                        labels=['<5.7', '5.7-6.5', '6.5-7', '7-8', '8-9', '9-10', '>10'])
bin_rates = df.groupby('a1c_bin', observed=True)['uncontrolled'].agg(['mean', 'count'])
bin_rates.columns = ['uncontrolled_rate', 'n_patients']

bars = ax.bar(range(len(bin_rates)), bin_rates['uncontrolled_rate'] * 100,
              color=['#2ecc71', '#82e0aa', '#f9e79f', '#f5b041', '#e67e22', '#e74c3c', '#c0392b'],
              edgecolor='black', linewidth=0.5)
ax.set_xticks(range(len(bin_rates)))
ax.set_xticklabels(bin_rates.index)
ax.set_xlabel('Current A1c Range')
ax.set_ylabel('% Who Become Uncontrolled in 2025')
ax.set_title('Step 2: Risk of Becoming Uncontrolled by Current A1c Level')

for i, (rate, n) in enumerate(zip(bin_rates['uncontrolled_rate'], bin_rates['n_patients'])):
    ax.text(i, rate * 100 + 1, f'{rate*100:.1f}%\n(n={n:,})', ha='center', fontsize=8)

plt.tight_layout()
plt.savefig('plots/step2_uncontrolled_rate_by_a1c_bin.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: plots/step2_uncontrolled_rate_by_a1c_bin.png")

print("\n--- Uncontrolled rate by A1c bin ---")
for idx, row in bin_rates.iterrows():
    print(f"  {idx:>7s}:  {row['uncontrolled_rate']*100:5.1f}%  (n={row['n_patients']:>6,})")

# cleanup temp column
df.drop(columns=['a1c_bin'], inplace=True)

# ── Step 3: Explore features by group ─────────────────────────────────────────

print("\n\n")
print("=" * 60)
print("STEP 3: EXPLORE FEATURES BY GROUP")
print("=" * 60)

# --- 3a: Demographics ---
df['age'] = 2025 - df['date of birth']

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Age distribution by outcome
for label, color, name in [(0, '#2ecc71', 'Controlled'), (1, '#e74c3c', 'Uncontrolled')]:
    subset = df.loc[df['uncontrolled'] == label, 'age']
    axes[0, 0].hist(subset, bins=40, alpha=0.6, color=color, label=name, density=True, edgecolor='black', linewidth=0.3)
axes[0, 0].set_xlabel('Age')
axes[0, 0].set_ylabel('Density')
axes[0, 0].set_title('Age Distribution by Outcome')
axes[0, 0].legend()

# Uncontrolled rate by age bin
df['age_bin'] = pd.cut(df['age'], bins=[0, 30, 40, 50, 60, 70, 80, 120],
                        labels=['<30', '30-39', '40-49', '50-59', '60-69', '70-79', '80+'])
age_rates = df.groupby('age_bin', observed=True)['uncontrolled'].agg(['mean', 'count'])
axes[0, 1].bar(range(len(age_rates)), age_rates['mean'] * 100, color='#3498db', edgecolor='black', linewidth=0.5)
axes[0, 1].set_xticks(range(len(age_rates)))
axes[0, 1].set_xticklabels(age_rates.index)
axes[0, 1].set_xlabel('Age Group')
axes[0, 1].set_ylabel('% Uncontrolled')
axes[0, 1].set_title('Uncontrolled Rate by Age Group')
for i, (rate, n) in enumerate(zip(age_rates['mean'], age_rates['count'])):
    axes[0, 1].text(i, rate * 100 + 0.5, f'{rate*100:.1f}%\n(n={n:,})', ha='center', fontsize=7)

# Gender
gender_rates = df.groupby('gender at birth')['uncontrolled'].agg(['mean', 'count']).sort_values('count', ascending=False)
gender_rates = gender_rates[gender_rates['count'] >= 10]
axes[1, 0].barh(range(len(gender_rates)), gender_rates['mean'] * 100, color='#9b59b6', edgecolor='black', linewidth=0.5)
axes[1, 0].set_yticks(range(len(gender_rates)))
axes[1, 0].set_yticklabels(gender_rates.index)
axes[1, 0].set_xlabel('% Uncontrolled')
axes[1, 0].set_title('Uncontrolled Rate by Gender')
for i, (rate, n) in enumerate(zip(gender_rates['mean'], gender_rates['count'])):
    axes[1, 0].text(rate * 100 + 0.3, i, f'{rate*100:.1f}% (n={n:,})', va='center', fontsize=8)

# Race
race_rates = df.groupby('race - primary')['uncontrolled'].agg(['mean', 'count']).sort_values('mean', ascending=True)
race_rates = race_rates[race_rates['count'] >= 50]
axes[1, 1].barh(range(len(race_rates)), race_rates['mean'] * 100, color='#e67e22', edgecolor='black', linewidth=0.5)
axes[1, 1].set_yticks(range(len(race_rates)))
axes[1, 1].set_yticklabels(race_rates.index)
axes[1, 1].set_xlabel('% Uncontrolled')
axes[1, 1].set_title('Uncontrolled Rate by Race')
for i, (rate, n) in enumerate(zip(race_rates['mean'], race_rates['count'])):
    axes[1, 1].text(rate * 100 + 0.3, i, f'{rate*100:.1f}% (n={n:,})', va='center', fontsize=8)

plt.suptitle('Step 3: Demographics by Outcome', fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('plots/step3_demographics.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: plots/step3_demographics.png")

# --- 3b: Comorbidities + Medications ---
med_cols = ['glp-1 orders-count', 'insulin orders-count', 'metformin orders-count',
            'sglt2 orders-count', 'sulfonylurea orders-count', 'dpp4 orders-count']
med_labels = ['GLP-1', 'Insulin', 'Metformin', 'SGLT2', 'Sulfonylurea', 'DPP4']

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# CAD by outcome
cad_rates = df.groupby(df['cad-count'].clip(upper=3))['uncontrolled'].agg(['mean', 'count'])
cad_rates.index = [str(i) if i < 3 else '3+' for i in cad_rates.index]
axes[0, 0].bar(range(len(cad_rates)), cad_rates['mean'] * 100, color='#e74c3c', edgecolor='black', linewidth=0.5)
axes[0, 0].set_xticks(range(len(cad_rates)))
axes[0, 0].set_xticklabels(cad_rates.index)
axes[0, 0].set_xlabel('CAD Count')
axes[0, 0].set_ylabel('% Uncontrolled')
axes[0, 0].set_title('Uncontrolled Rate by CAD Count')
for i, (rate, n) in enumerate(zip(cad_rates['mean'], cad_rates['count'])):
    axes[0, 0].text(i, rate * 100 + 0.5, f'{rate*100:.1f}%\n(n={n:,})', ha='center', fontsize=7)

# COPD by outcome
copd_rates = df.groupby(df['copd-count'].clip(upper=3))['uncontrolled'].agg(['mean', 'count'])
copd_rates.index = [str(i) if i < 3 else '3+' for i in copd_rates.index]
axes[0, 1].bar(range(len(copd_rates)), copd_rates['mean'] * 100, color='#e74c3c', edgecolor='black', linewidth=0.5)
axes[0, 1].set_xticks(range(len(copd_rates)))
axes[0, 1].set_xticklabels(copd_rates.index)
axes[0, 1].set_xlabel('COPD Count')
axes[0, 1].set_ylabel('% Uncontrolled')
axes[0, 1].set_title('Uncontrolled Rate by COPD Count')
for i, (rate, n) in enumerate(zip(copd_rates['mean'], copd_rates['count'])):
    axes[0, 1].text(i, rate * 100 + 0.5, f'{rate*100:.1f}%\n(n={n:,})', ha='center', fontsize=7)

# Medication usage by outcome
controlled_pct = [(df.loc[df['uncontrolled'] == 0, c] > 0).mean() * 100 for c in med_cols]
uncontrolled_pct = [(df.loc[df['uncontrolled'] == 1, c] > 0).mean() * 100 for c in med_cols]
x = np.arange(len(med_labels))
w = 0.35
axes[1, 0].bar(x - w / 2, controlled_pct, w, label='Controlled', color='#2ecc71', edgecolor='black', linewidth=0.5)
axes[1, 0].bar(x + w / 2, uncontrolled_pct, w, label='Uncontrolled', color='#e74c3c', edgecolor='black', linewidth=0.5)
axes[1, 0].set_xticks(x)
axes[1, 0].set_xticklabels(med_labels, rotation=30, ha='right')
axes[1, 0].set_ylabel('% of patients with any orders')
axes[1, 0].set_title('Medication Use by Outcome')
axes[1, 0].legend()

# Uncontrolled rate by total med classes
df['total_med_classes'] = (df[med_cols] > 0).sum(axis=1)
med_class_rates = df.groupby('total_med_classes')['uncontrolled'].agg(['mean', 'count'])
axes[1, 1].bar(med_class_rates.index, med_class_rates['mean'] * 100, color='#3498db', edgecolor='black', linewidth=0.5)
axes[1, 1].set_xlabel('Number of Medication Classes')
axes[1, 1].set_ylabel('% Uncontrolled')
axes[1, 1].set_title('Uncontrolled Rate by # of Med Classes')
for i, (idx, row) in enumerate(med_class_rates.iterrows()):
    axes[1, 1].text(idx, row['mean'] * 100 + 0.5, f'{row["mean"]*100:.1f}%\n(n={row["count"]:,})', ha='center', fontsize=7)

plt.suptitle('Step 3: Comorbidities & Medications by Outcome', fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('plots/step3_comorbidities_meds.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: plots/step3_comorbidities_meds.png")

# --- 3c: Utilization, Cholesterol, ADI ---
fig, axes = plt.subplots(2, 3, figsize=(18, 10))

# ED visits
ed_bins = df['ed vist count-count'].clip(upper=5)
ed_rates = df.groupby(ed_bins)['uncontrolled'].agg(['mean', 'count'])
ed_rates.index = [str(int(i)) if i < 5 else '5+' for i in ed_rates.index]
axes[0, 0].bar(range(len(ed_rates)), ed_rates['mean'] * 100, color='#3498db', edgecolor='black', linewidth=0.5)
axes[0, 0].set_xticks(range(len(ed_rates)))
axes[0, 0].set_xticklabels(ed_rates.index)
axes[0, 0].set_xlabel('ED Visits')
axes[0, 0].set_ylabel('% Uncontrolled')
axes[0, 0].set_title('Uncontrolled Rate by ED Visits')
for i, (rate, n) in enumerate(zip(ed_rates['mean'], ed_rates['count'])):
    axes[0, 0].text(i, rate * 100 + 0.5, f'{rate*100:.1f}%\n(n={n:,})', ha='center', fontsize=6)

# PCP visits
pcp_bins = df['pcp visit count-count'].clip(upper=5)
pcp_rates = df.groupby(pcp_bins)['uncontrolled'].agg(['mean', 'count'])
pcp_rates.index = [str(int(i)) if i < 5 else '5+' for i in pcp_rates.index]
axes[0, 1].bar(range(len(pcp_rates)), pcp_rates['mean'] * 100, color='#3498db', edgecolor='black', linewidth=0.5)
axes[0, 1].set_xticks(range(len(pcp_rates)))
axes[0, 1].set_xticklabels(pcp_rates.index)
axes[0, 1].set_xlabel('PCP Visits')
axes[0, 1].set_ylabel('% Uncontrolled')
axes[0, 1].set_title('Uncontrolled Rate by PCP Visits')
for i, (rate, n) in enumerate(zip(pcp_rates['mean'], pcp_rates['count'])):
    axes[0, 1].text(i, rate * 100 + 0.5, f'{rate*100:.1f}%\n(n={n:,})', ha='center', fontsize=6)

# Admissions
adm_bins = df['admission count-count'].clip(upper=3)
adm_rates = df.groupby(adm_bins)['uncontrolled'].agg(['mean', 'count'])
adm_rates.index = [str(int(i)) if i < 3 else '3+' for i in adm_rates.index]
axes[0, 2].bar(range(len(adm_rates)), adm_rates['mean'] * 100, color='#3498db', edgecolor='black', linewidth=0.5)
axes[0, 2].set_xticks(range(len(adm_rates)))
axes[0, 2].set_xticklabels(adm_rates.index)
axes[0, 2].set_xlabel('Admissions')
axes[0, 2].set_ylabel('% Uncontrolled')
axes[0, 2].set_title('Uncontrolled Rate by Admissions')
for i, (rate, n) in enumerate(zip(adm_rates['mean'], adm_rates['count'])):
    axes[0, 2].text(i, rate * 100 + 0.5, f'{rate*100:.1f}%\n(n={n:,})', ha='center', fontsize=6)

# LDL
for label, color, name in [(0, '#2ecc71', 'Controlled'), (1, '#e74c3c', 'Uncontrolled')]:
    s = df.loc[df['uncontrolled'] == label, 'ldl-estimated result'].dropna()
    axes[1, 0].hist(s, bins=50, alpha=0.6, color=color, label=name, density=True, edgecolor='black', linewidth=0.3)
axes[1, 0].set_xlabel('LDL (mg/dL)')
axes[1, 0].set_ylabel('Density')
axes[1, 0].set_title('LDL Distribution by Outcome')
axes[1, 0].legend()

# HDL
for label, color, name in [(0, '#2ecc71', 'Controlled'), (1, '#e74c3c', 'Uncontrolled')]:
    s = df.loc[df['uncontrolled'] == label, 'hdl-estimated result'].dropna()
    axes[1, 1].hist(s, bins=50, alpha=0.6, color=color, label=name, density=True, edgecolor='black', linewidth=0.3)
axes[1, 1].set_xlabel('HDL (mg/dL)')
axes[1, 1].set_ylabel('Density')
axes[1, 1].set_title('HDL Distribution by Outcome')
axes[1, 1].legend()

# ADI
df['adi_national'] = pd.to_numeric(df['adi-adi national rank'], errors='coerce')
for label, color, name in [(0, '#2ecc71', 'Controlled'), (1, '#e74c3c', 'Uncontrolled')]:
    s = df.loc[df['uncontrolled'] == label, 'adi_national'].dropna()
    axes[1, 2].hist(s, bins=30, alpha=0.6, color=color, label=name, density=True, edgecolor='black', linewidth=0.3)
axes[1, 2].set_xlabel('ADI National Rank (higher = more deprived)')
axes[1, 2].set_ylabel('Density')
axes[1, 2].set_title('ADI National Rank by Outcome')
axes[1, 2].legend()

plt.suptitle('Step 3: Utilization, Cholesterol & ADI by Outcome', fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('plots/step3_util_chol_adi.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: plots/step3_util_chol_adi.png")

# cleanup temp columns
df.drop(columns=['age_bin', 'total_med_classes', 'adi_national'], inplace=True)

# ── Step 4: Map missingness ───────────────────────────────────────────────────

print("\n\n")
print("=" * 60)
print("STEP 4: MAP MISSINGNESS")
print("=" * 60)

sns.set_style('whitegrid')

missing = features.isnull().sum()
miss_cols = missing[missing > 0].sort_values(ascending=False).index.tolist()

short_names = {c: c.replace('-estimated result', '').replace('-collection date-time-days from reference', ' (date)')
                .replace('-measurement date-time-days from reference', ' (date)')
                .replace('-unit of measure', ' (unit)')
                .replace('payor first op visit-primary insurance plan', 'insurance')
                .replace('adi-adi ', 'adi ')
               for c in miss_cols}

# Plot 1: Missingness heatmap
fig, ax = plt.subplots(figsize=(14, 6))
sample = features[miss_cols].sample(500, random_state=42)
sample_sorted = sample.loc[sample.isnull().sum(axis=1).sort_values(ascending=False).index]
sns.heatmap(sample_sorted.isnull().astype(int).values, cmap=['#2ecc71', '#e74c3c'],
            xticklabels=[short_names[c] for c in miss_cols], yticklabels=False,
            cbar_kws={'label': 'Missing', 'ticks': [0, 1]}, ax=ax)
ax.set_xlabel('Feature')
ax.set_title('Step 4: Missingness Pattern (500 random patients, sorted by # missing)')
plt.xticks(rotation=45, ha='right', fontsize=8)
plt.tight_layout()
plt.savefig('plots/step4_missingness_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: plots/step4_missingness_heatmap.png")

# Plot 2: Missingness rate by outcome
fig, ax = plt.subplots(figsize=(12, 7))
controlled_miss = df.loc[df['uncontrolled'] == 0, miss_cols].isnull().mean() * 100
uncontrolled_miss = df.loc[df['uncontrolled'] == 1, miss_cols].isnull().mean() * 100

y_pos = np.arange(len(miss_cols))
w = 0.35
ax.barh(y_pos - w / 2, controlled_miss, w, label='Controlled', color='#2ecc71', edgecolor='black', linewidth=0.3)
ax.barh(y_pos + w / 2, uncontrolled_miss, w, label='Uncontrolled', color='#e74c3c', edgecolor='black', linewidth=0.3)
ax.set_yticks(y_pos)
ax.set_yticklabels([short_names[c] for c in miss_cols], fontsize=8)
ax.set_xlabel('% Missing')
ax.set_title('Step 4: Missingness Rate by Outcome')
ax.legend()
ax.invert_yaxis()
plt.tight_layout()
plt.savefig('plots/step4_missingness_by_outcome.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: plots/step4_missingness_by_outcome.png")

# ── Step 5: Check correlations ────────────────────────────────────────────────

print("\n\n")
print("=" * 60)
print("STEP 5: CHECK CORRELATIONS")
print("=" * 60)

# Convert ADI to numeric
df['adi_state'] = pd.to_numeric(df['adi-adi state rank'], errors='coerce')
df['adi_national'] = pd.to_numeric(df['adi-adi national rank'], errors='coerce')

# Select numeric columns (drop date/timing, units, leakage)
drop_patterns = ['date-time', 'unit of measure', 'a1c 2025-collection']
num_cols = [c for c in df.select_dtypes(include=[np.number]).columns
            if not any(p in c for p in drop_patterns)]

rename_map = {
    'date of birth': 'birth_year', 'cad-count': 'cad', 'copd-count': 'copd',
    'a1c 1-estimated result': 'a1c_1', 'a1c 2-estimated result': 'a1c_2',
    'a1c 3-estimated result': 'a1c_3', 'a1c 4-estimated result': 'a1c_4',
    'a1c 5-estimated result': 'a1c_5', 'weight-estimated result': 'weight',
    'height-estimated result': 'height', 'ldl-estimated result': 'ldl',
    'hdl-estimated result': 'hdl', 'total cholesterol-estimated result': 'total_chol',
    'ed vist count-count': 'ed_visits', 'pcp visit count-count': 'pcp_visits',
    'glp-1 orders-count': 'glp1', 'insulin orders-count': 'insulin',
    'metformin orders-count': 'metformin', 'sglt2 orders-count': 'sglt2',
    'sulfonylurea orders-count': 'sulfonylurea', 'dpp4 orders-count': 'dpp4',
    'admission count-count': 'admissions', 'uncontrolled': 'UNCONTROLLED',
}
corr_df = df[num_cols].rename(columns=rename_map)
corr = corr_df.corr()

# Plot 1: Correlation heatmap
fig, ax = plt.subplots(figsize=(16, 14))
mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
            vmin=-1, vmax=1, square=True, linewidths=0.5,
            annot_kws={'size': 7}, ax=ax)
ax.set_title('Step 5: Correlation Matrix (numeric features + target)', fontweight='bold', fontsize=14)
plt.xticks(rotation=45, ha='right', fontsize=9)
plt.yticks(fontsize=9)
plt.tight_layout()
plt.savefig('plots/step5_correlation_matrix.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: plots/step5_correlation_matrix.png")

# Plot 2: Correlations with target
target_corr = corr['UNCONTROLLED'].drop('UNCONTROLLED').sort_values()
fig, ax = plt.subplots(figsize=(10, 8))
colors = ['#e74c3c' if v > 0 else '#3498db' for v in target_corr]
ax.barh(range(len(target_corr)), target_corr.values, color=colors, edgecolor='black', linewidth=0.3)
ax.set_yticks(range(len(target_corr)))
ax.set_yticklabels(target_corr.index, fontsize=9)
ax.set_xlabel('Pearson Correlation with Uncontrolled')
ax.set_title('Step 5: Feature Correlation with Target (Uncontrolled)', fontweight='bold')
ax.axvline(x=0, color='black', linewidth=0.8)
for i, v in enumerate(target_corr.values):
    ax.text(v + (0.005 if v >= 0 else -0.005), i, f'{v:.3f}',
            va='center', ha='left' if v >= 0 else 'right', fontsize=8)
plt.tight_layout()
plt.savefig('plots/step5_target_correlations.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: plots/step5_target_correlations.png")

# cleanup
df.drop(columns=['adi_state', 'adi_national'], inplace=True)
