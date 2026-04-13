"""
Step 8: Train-test split.
Reads DM_Features_engineered.csv + DM_Control_2025.csv
-> drops raw columns replaced by engineered features
-> 80/20 stratified split (random_state=42)
-> saves X_train.csv, X_test.csv, y_train.csv, y_test.csv

Feature matrix: 48 columns (39 zero-missing, 9 with missing values)
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

df = pd.read_csv('data/processed/DM_Features_engineered.csv', index_col=0)
target = pd.read_csv('data/raw/DM Control_2025.csv', index_col=0)
y = target['a1c 2025 Uncontrolled'].astype(int)

# Drop raw columns now captured by engineered features
raw_a1c = ['a1c 1-estimated result', 'a1c 2-estimated result', 'a1c 3-estimated result',
           'a1c 4-estimated result', 'a1c 5-estimated result']
raw_drop = raw_a1c + ['date of birth', 'weight-estimated result', 'height-estimated result']
X = df.drop(columns=raw_drop)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

X_train.to_csv('internal_validation/X_train.csv')
X_test.to_csv('internal_validation/X_test.csv')
y_train.to_csv('internal_validation/y_train.csv')
y_test.to_csv('internal_validation/y_test.csv')

print(f'Train: {X_train.shape[0]:,} x {X_train.shape[1]} | Test: {X_test.shape[0]:,} x {X_test.shape[1]}')
print(f'Train uncontrolled: {y_train.mean()*100:.2f}% | Test uncontrolled: {y_test.mean()*100:.2f}%')
