"""
Step 6: Clean the raw features data.
Reads DM Features.csv -> applies all cleaning -> saves DM_Features_cleaned.csv

Cleaning steps:
  1. Drop leakage column (a1c 2025 collection date)
  2. Drop date/timing columns (10 cols)
  3. Drop unit-of-measure columns (2 cols) -- all weights are kg, heights are cm
  4. Drop adi state rank (redundant with national, r=0.96)
  5. Convert adi national rank from string to numeric
  6. Encode gender -> is_male (0/1)
  7. Encode ethnicity -> is_hispanic (0/1)
  8. One-hot encode race (7 categories)
  9. Simplify + one-hot encode insurance (4 categories: Managed Care, Medicaid, Medicare, Other)

Result: 62,425 rows x 36 columns, all numeric
"""

import pandas as pd
import numpy as np

features = pd.read_csv('data/raw/DM Features.csv', index_col=0)
print(f'Raw shape: {features.shape}')

# 1. Drop leakage column
features.drop(columns=['a1c 2025-collection date-time-days from reference'], inplace=True)

# 2. Drop date/timing columns
date_cols = [c for c in features.columns if 'date-time-days' in c or 'measurement date-time' in c]
features.drop(columns=date_cols, inplace=True)

# 3. Drop unit-of-measure columns
unit_cols = [c for c in features.columns if 'unit of measure' in c]
features.drop(columns=unit_cols, inplace=True)

# 4. Drop redundant ADI state rank
features.drop(columns=['adi-adi state rank'], inplace=True)

# 5. Fix ADI national rank dtype
features['adi-adi national rank'] = pd.to_numeric(features['adi-adi national rank'], errors='coerce')

# 6. Gender -> is_male
features['is_male'] = (features['gender at birth'] == 'MALE').astype(int)
features.loc[features['gender at birth'].isna(), 'is_male'] = np.nan
features.drop(columns=['gender at birth'], inplace=True)

# 7. Ethnicity -> is_hispanic
features['is_hispanic'] = (features['ethnicity'] == 'Hispanic or Latino').astype(int)
features.loc[features['ethnicity'].isna(), 'is_hispanic'] = np.nan
features.drop(columns=['ethnicity'], inplace=True)

# 8. One-hot encode race
race_dummies = pd.get_dummies(features['race - primary'], prefix='race', dtype=int)
features = pd.concat([features, race_dummies], axis=1)
features.drop(columns=['race - primary'], inplace=True)

# 9. Simplify + one-hot encode insurance
ins_col = 'payor first op visit-primary insurance plan'
ins = features[ins_col].copy()
ins_map = {}
for val in ins.dropna().unique():
    vl = val.lower()
    if 'medicare' in vl:
        ins_map[val] = 'Medicare'
    elif 'medicaid' in vl:
        ins_map[val] = 'Medicaid'
    elif any(x in vl for x in ['managed care', 'hmo', 'ppo', 'blue']):
        ins_map[val] = 'Managed Care'
    else:
        ins_map[val] = 'Other'
ins_dummies = pd.get_dummies(ins.map(ins_map), prefix='insurance', dtype=int)
features = pd.concat([features, ins_dummies], axis=1)
features.drop(columns=[ins_col], inplace=True)

# Save
features.to_csv('data/processed/DM_Features_cleaned.csv')
print(f'Cleaned shape: {features.shape}')
print(f'Saved: DM_Features_cleaned.csv')
