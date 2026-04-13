"""
Step 2: Retrain XGBoost on 100% of training data using tuned hyperparameters.
Pipeline: raw CSV -> clean -> engineer features -> train -> save model
"""

import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from xgboost import XGBClassifier
import pickle

# ── Load raw data ────────────────────────────────────────────────────────────
features = pd.read_csv('data/raw/DM Features.csv', index_col=0)
target = pd.read_csv('data/raw/DM Control_2025.csv', index_col=0).squeeze()
print(f'Raw features: {features.shape}')
print(f'Target: {target.shape}, uncontrolled rate: {target.mean():.1%}')

# ── Clean (same as clean_data.py) ────────────────────────────────────────────

# Drop leakage column
features.drop(columns=['a1c 2025-collection date-time-days from reference'], inplace=True)

# Drop date/timing columns
date_cols = [c for c in features.columns if 'date-time-days' in c or 'measurement date-time' in c]
features.drop(columns=date_cols, inplace=True)

# Drop unit-of-measure columns
unit_cols = [c for c in features.columns if 'unit of measure' in c]
features.drop(columns=unit_cols, inplace=True)

# Drop redundant ADI state rank
features.drop(columns=['adi-adi state rank'], inplace=True)

# Fix ADI national rank dtype
features['adi-adi national rank'] = pd.to_numeric(features['adi-adi national rank'], errors='coerce')

# Gender -> is_male
features['is_male'] = (features['gender at birth'] == 'MALE').astype(int)
features.loc[features['gender at birth'].isna(), 'is_male'] = np.nan
features.drop(columns=['gender at birth'], inplace=True)

# Ethnicity -> is_hispanic
features['is_hispanic'] = (features['ethnicity'] == 'Hispanic or Latino').astype(int)
features.loc[features['ethnicity'].isna(), 'is_hispanic'] = np.nan
features.drop(columns=['ethnicity'], inplace=True)

# One-hot encode race
race_dummies = pd.get_dummies(features['race - primary'], prefix='race', dtype=int)
features = pd.concat([features, race_dummies], axis=1)
features.drop(columns=['race - primary'], inplace=True)

# Simplify + one-hot encode insurance
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

print(f'Cleaned: {features.shape}')

# ── Engineer features (same as feature_engineering.py) ───────────────────────

a1c_cols = ['a1c 1-estimated result', 'a1c 2-estimated result', 'a1c 3-estimated result',
            'a1c 4-estimated result', 'a1c 5-estimated result']
med_cols = ['glp-1 orders-count', 'insulin orders-count', 'metformin orders-count',
            'sglt2 orders-count', 'sulfonylurea orders-count', 'dpp4 orders-count']

a1c_df = features[a1c_cols]
n_tests = a1c_df.notna().sum(axis=1)

# HIGH priority
features['age'] = 2025 - features['date of birth']
features['a1c_latest'] = features['a1c 1-estimated result']

def get_oldest_a1c(row):
    for col in reversed(a1c_cols):
        if pd.notna(row[col]):
            return row[col]
    return np.nan

oldest = a1c_df.apply(get_oldest_a1c, axis=1)
features['a1c_change'] = np.where(n_tests >= 2, features['a1c 1-estimated result'] - oldest, np.nan)
features['n_a1c_tests'] = n_tests
features['a1c_mean'] = a1c_df.mean(axis=1)
features['total_med_classes'] = (features[med_cols] > 0).sum(axis=1)

# MEDIUM priority
features['a1c_max'] = a1c_df.max(axis=1)
features['a1c_variability'] = a1c_df.std(axis=1)
features['a1c_above_9'] = (features['a1c_latest'] >= 9).astype(int)
features['total_med_orders'] = features[med_cols].sum(axis=1)
features['on_insulin'] = (features['insulin orders-count'] > 0).astype(int)
features['on_newer_drugs'] = ((features['glp-1 orders-count'] > 0) | (features['sglt2 orders-count'] > 0)).astype(int)
features['no_medication'] = (features['total_med_classes'] == 0).astype(int)

height_m = features['height-estimated result'] / 100
features['bmi'] = features['weight-estimated result'] / (height_m ** 2)
features.loc[features['bmi'] > 80, 'bmi'] = np.nan
features.loc[features['bmi'] < 10, 'bmi'] = np.nan
features['has_bmi'] = features['bmi'].notna().astype(int)

features['total_encounters'] = features['ed vist count-count'] + features['pcp visit count-count'] + features['admission count-count']
features['any_admission'] = (features['admission count-count'] > 0).astype(int)
features['any_comorbidity'] = ((features['cad-count'] > 0) | (features['copd-count'] > 0)).astype(int)
features['undertreated'] = ((features['a1c_latest'] >= 8) & (features['total_med_classes'] == 0)).astype(int)
features['treatment_resistant'] = ((features['a1c_latest'] >= 8) & (features['total_med_classes'] >= 2)).astype(int)

print(f'Engineered: {features.shape}')

# ── Impute + Train on 100% ──────────────────────────────────────────────────

# Align target
y = target.loc[features.index].astype(int)
print(f'Target aligned: {y.shape}, uncontrolled: {y.sum()} ({y.mean():.1%})')

# Impute missing values
imputer = SimpleImputer(strategy='median')
X = pd.DataFrame(imputer.fit_transform(features), columns=features.columns, index=features.index)

# Save column order (needed for test set)
col_order = list(X.columns)

# Train XGBoost with tuned hyperparameters
scale = (y == 0).sum() / (y == 1).sum()
print(f'scale_pos_weight: {scale:.2f}')

model = XGBClassifier(
    n_estimators=800,
    max_depth=5,
    learning_rate=0.01,
    subsample=0.7,
    colsample_bytree=0.5,
    min_child_weight=10,
    gamma=0.3,
    reg_lambda=1,
    reg_alpha=0,
    scale_pos_weight=scale,
    eval_metric='logloss',
    n_jobs=-1,
    random_state=42,
)

model.fit(X, y)
print(f'Model trained on {X.shape[0]} patients, {X.shape[1]} features')

# Save model, imputer, and column order
pickle.dump({
    'model': model,
    'imputer': imputer,
    'columns': col_order,
}, open('models/xgb_final_model.pkl', 'wb'))
print('Saved: models/xgb_final_model.pkl')
