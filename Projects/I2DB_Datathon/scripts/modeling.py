"""
Steps 9-12: Model building and evaluation.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (roc_auc_score, classification_report, confusion_matrix,
                             roc_curve, precision_recall_curve, average_precision_score)

sns.set_style('whitegrid')

X_train = pd.read_csv('internal_validation/X_train.csv', index_col=0)
X_test = pd.read_csv('internal_validation/X_test.csv', index_col=0)
y_train = pd.read_csv('internal_validation/y_train.csv', index_col=0).squeeze()
y_test = pd.read_csv('internal_validation/y_test.csv', index_col=0).squeeze()

# ── Step 9: Baseline logistic regression ──────────────────────────────────────

high_feats = ['age', 'a1c_latest', 'a1c_change', 'n_a1c_tests', 'a1c_mean', 'total_med_classes']

# Model 1: HIGH features only
pipe_high = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler()),
    ('model', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42))
])
pipe_high.fit(X_train[high_feats], y_train)

# Model 2: ALL features
pipe_all = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler()),
    ('model', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42))
])
pipe_all.fit(X_train, y_train)

# Evaluate both
for name, pipe, feats in [('HIGH (6 feat)', pipe_high, high_feats), ('ALL (48 feat)', pipe_all, X_test.columns)]:
    y_prob = pipe.predict_proba(X_test[feats])[:, 1]
    auc = roc_auc_score(y_test, y_prob)
    ap = average_precision_score(y_test, y_prob)
    print(f'{name}: AUC={auc:.4f}, AP={ap:.4f}')
