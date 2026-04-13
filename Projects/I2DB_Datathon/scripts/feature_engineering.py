"""
Step 7: Feature engineering.
Reads DM_Features_cleaned.csv -> engineers 20 new features -> saves DM_Features_engineered.csv

HIGH priority (6):  age, a1c_latest, a1c_change, n_a1c_tests, a1c_mean, total_med_classes
MEDIUM priority (14): a1c_max, a1c_variability, a1c_above_9, total_med_orders, on_insulin,
                      on_newer_drugs, no_medication, bmi, has_bmi, total_encounters,
                      any_admission, any_comorbidity, undertreated, treatment_resistant

Result: 62,425 rows x 56 columns
"""

import pandas as pd
import numpy as np

df = pd.read_csv('data/processed/DM_Features_cleaned.csv', index_col=0)
print(f'Input shape: {df.shape}')

a1c_cols = ['a1c 1-estimated result', 'a1c 2-estimated result', 'a1c 3-estimated result',
            'a1c 4-estimated result', 'a1c 5-estimated result']
med_cols = ['glp-1 orders-count', 'insulin orders-count', 'metformin orders-count',
            'sglt2 orders-count', 'sulfonylurea orders-count', 'dpp4 orders-count']

a1c_df = df[a1c_cols]
n_tests = a1c_df.notna().sum(axis=1)

# --- HIGH priority ---
df['age'] = 2025 - df['date of birth']
df['a1c_latest'] = df['a1c 1-estimated result']

def get_oldest_a1c(row):
    for col in reversed(a1c_cols):
        if pd.notna(row[col]):
            return row[col]
    return np.nan

oldest = a1c_df.apply(get_oldest_a1c, axis=1)
df['a1c_change'] = np.where(n_tests >= 2, df['a1c 1-estimated result'] - oldest, np.nan)
df['n_a1c_tests'] = n_tests
df['a1c_mean'] = a1c_df.mean(axis=1)
df['total_med_classes'] = (df[med_cols] > 0).sum(axis=1)

# --- MEDIUM priority ---
df['a1c_max'] = a1c_df.max(axis=1)
df['a1c_variability'] = a1c_df.std(axis=1)
df['a1c_above_9'] = (df['a1c_latest'] >= 9).astype(int)
df['total_med_orders'] = df[med_cols].sum(axis=1)
df['on_insulin'] = (df['insulin orders-count'] > 0).astype(int)
df['on_newer_drugs'] = ((df['glp-1 orders-count'] > 0) | (df['sglt2 orders-count'] > 0)).astype(int)
df['no_medication'] = (df['total_med_classes'] == 0).astype(int)

height_m = df['height-estimated result'] / 100
df['bmi'] = df['weight-estimated result'] / (height_m ** 2)
df.loc[df['bmi'] > 80, 'bmi'] = np.nan
df.loc[df['bmi'] < 10, 'bmi'] = np.nan
df['has_bmi'] = df['bmi'].notna().astype(int)

df['total_encounters'] = df['ed vist count-count'] + df['pcp visit count-count'] + df['admission count-count']
df['any_admission'] = (df['admission count-count'] > 0).astype(int)
df['any_comorbidity'] = ((df['cad-count'] > 0) | (df['copd-count'] > 0)).astype(int)
df['undertreated'] = ((df['a1c_latest'] >= 8) & (df['total_med_classes'] == 0)).astype(int)
df['treatment_resistant'] = ((df['a1c_latest'] >= 8) & (df['total_med_classes'] >= 2)).astype(int)

# Save
df.to_csv('data/processed/DM_Features_engineered.csv')
print(f'Output shape: {df.shape}')
print(f'Saved: DM_Features_engineered.csv')
