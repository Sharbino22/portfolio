"""
Final Step: Apply pipeline to competition test set and generate submission.
- Loads the 100%-trained XGBoost model
- Cleans + engineers features on the test set (same pipeline as training)
- Predicts using 0.50 threshold (sensitivity-prioritized for clinical screening)
- Compares prediction distributions against internal validation as sanity check
- Saves submission/final_submission.csv
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
from sklearn.metrics import roc_auc_score

sns.set_style('whitegrid')

THRESHOLD = 0.50

# ── Load final model bundle ──────────────────────────────────────────────────
bundle = pickle.load(open('models/xgb_final_model.pkl', 'rb'))
model = bundle['model']
imputer = bundle['imputer']
col_order = bundle['columns']

# ── Load and clean test set (same pipeline as training) ──────────────────────
test = pd.read_csv('data/raw/TEST_SET_DM_Features.csv', index_col=0)
print("Raw test set: {}".format(test.shape))

# Drop leakage column
if 'a1c 2025-collection date-time-days from reference' in test.columns:
    test.drop(columns=['a1c 2025-collection date-time-days from reference'], inplace=True)

# Drop date/timing columns
date_cols = [c for c in test.columns if 'date-time-days' in c or 'measurement date-time' in c]
test.drop(columns=date_cols, inplace=True)

# Drop unit-of-measure columns
unit_cols = [c for c in test.columns if 'unit of measure' in c]
test.drop(columns=unit_cols, inplace=True)

# Drop redundant ADI state rank
test.drop(columns=['adi-adi state rank'], inplace=True)

# Fix ADI national rank dtype
test['adi-adi national rank'] = pd.to_numeric(test['adi-adi national rank'], errors='coerce')

# Gender -> is_male
test['is_male'] = (test['gender at birth'] == 'MALE').astype(int)
test.loc[test['gender at birth'].isna(), 'is_male'] = np.nan
test.drop(columns=['gender at birth'], inplace=True)

# Ethnicity -> is_hispanic
test['is_hispanic'] = (test['ethnicity'] == 'Hispanic or Latino').astype(int)
test.loc[test['ethnicity'].isna(), 'is_hispanic'] = np.nan
test.drop(columns=['ethnicity'], inplace=True)

# One-hot encode race
race_dummies = pd.get_dummies(test['race - primary'], prefix='race', dtype=int)
test = pd.concat([test, race_dummies], axis=1)
test.drop(columns=['race - primary'], inplace=True)

# Simplify + one-hot encode insurance
ins_col = 'payor first op visit-primary insurance plan'
ins = test[ins_col].copy()
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
test = pd.concat([test, ins_dummies], axis=1)
test.drop(columns=[ins_col], inplace=True)

print("Cleaned test: {}".format(test.shape))

# ── Engineer features ────────────────────────────────────────────────────────
a1c_cols = ['a1c 1-estimated result', 'a1c 2-estimated result', 'a1c 3-estimated result',
            'a1c 4-estimated result', 'a1c 5-estimated result']
med_cols = ['glp-1 orders-count', 'insulin orders-count', 'metformin orders-count',
            'sglt2 orders-count', 'sulfonylurea orders-count', 'dpp4 orders-count']

a1c_df = test[a1c_cols]
n_tests = a1c_df.notna().sum(axis=1)

# HIGH priority
test['age'] = 2025 - test['date of birth']
test['a1c_latest'] = test['a1c 1-estimated result']

def get_oldest_a1c(row):
    for col in reversed(a1c_cols):
        if pd.notna(row[col]):
            return row[col]
    return np.nan

oldest = a1c_df.apply(get_oldest_a1c, axis=1)
test['a1c_change'] = np.where(n_tests >= 2, test['a1c 1-estimated result'] - oldest, np.nan)
test['n_a1c_tests'] = n_tests
test['a1c_mean'] = a1c_df.mean(axis=1)
test['total_med_classes'] = (test[med_cols] > 0).sum(axis=1)

# MEDIUM priority
test['a1c_max'] = a1c_df.max(axis=1)
test['a1c_variability'] = a1c_df.std(axis=1)
test['a1c_above_9'] = (test['a1c_latest'] >= 9).astype(int)
test['total_med_orders'] = test[med_cols].sum(axis=1)
test['on_insulin'] = (test['insulin orders-count'] > 0).astype(int)
test['on_newer_drugs'] = ((test['glp-1 orders-count'] > 0) | (test['sglt2 orders-count'] > 0)).astype(int)
test['no_medication'] = (test['total_med_classes'] == 0).astype(int)

height_m = test['height-estimated result'] / 100
test['bmi'] = test['weight-estimated result'] / (height_m ** 2)
test.loc[test['bmi'] > 80, 'bmi'] = np.nan
test.loc[test['bmi'] < 10, 'bmi'] = np.nan
test['has_bmi'] = test['bmi'].notna().astype(int)

test['total_encounters'] = test['ed vist count-count'] + test['pcp visit count-count'] + test['admission count-count']
test['any_admission'] = (test['admission count-count'] > 0).astype(int)
test['any_comorbidity'] = ((test['cad-count'] > 0) | (test['copd-count'] > 0)).astype(int)
test['undertreated'] = ((test['a1c_latest'] >= 8) & (test['total_med_classes'] == 0)).astype(int)
test['treatment_resistant'] = ((test['a1c_latest'] >= 8) & (test['total_med_classes'] >= 2)).astype(int)

print("Engineered test: {}".format(test.shape))

# ── Align columns with training ─────────────────────────────────────────────
for col in col_order:
    if col not in test.columns:
        test[col] = 0
        print("  Added missing column: {} (set to 0)".format(col))

extra = [c for c in test.columns if c not in col_order]
if extra:
    test.drop(columns=extra, inplace=True)
    print("  Dropped extra columns: {}".format(extra))

test = test[col_order]
print("Final test shape: {} (should be 15607 x {})".format(test.shape, len(col_order)))

# ── Impute and predict ───────────────────────────────────────────────────────
X_test_imputed = pd.DataFrame(imputer.transform(test), columns=col_order, index=test.index)
test_probs = model.predict_proba(X_test_imputed)[:, 1]
test_preds = (test_probs >= THRESHOLD).astype(bool)

# ── Load internal validation for comparison ──────────────────────────────────
X_val = pd.read_csv('internal_validation/X_test.csv', index_col=0)
y_val = pd.read_csv('internal_validation/y_test.csv', index_col=0).squeeze()

X_val_aligned = X_val.reindex(columns=col_order, fill_value=0)
X_val_imputed = pd.DataFrame(imputer.transform(X_val_aligned), columns=col_order, index=X_val.index)
val_probs = model.predict_proba(X_val_imputed)[:, 1]
val_preds = (val_probs >= THRESHOLD).astype(bool)

# ══════════════════════════════════════════════════════════════════════════════
# COMPARISON REPORT
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("COMPARISON: Internal Validation vs Competition Test Set")
print("Threshold: {}".format(THRESHOLD))
print("=" * 70)

# 1. Predicted rates
val_rate = val_preds.mean()
test_rate = test_preds.mean()
print("\n1. PREDICTED UNCONTROLLED RATE")
print("   Training base rate (known):  10.6%")
print("   Internal val (20% holdout):  {:.1%}  (n={:,})".format(val_rate, len(val_preds)))
print("   Competition test set:        {:.1%}  (n={:,})".format(test_rate, len(test_preds)))

# 2. Probability distribution stats
print("\n2. PREDICTED PROBABILITY DISTRIBUTION")
print("   {:<20} {:>15} {:>15}".format("Statistic", "Internal Val", "Comp. Test"))
print("   {} {} {}".format("-" * 20, "-" * 15, "-" * 15))
for name, func in [('Mean', np.mean), ('Median', np.median), ('Std', np.std),
                    ('25th pctl', lambda x: np.percentile(x, 25)),
                    ('75th pctl', lambda x: np.percentile(x, 75)),
                    ('90th pctl', lambda x: np.percentile(x, 90)),
                    ('95th pctl', lambda x: np.percentile(x, 95))]:
    print("   {:<20} {:>15.4f} {:>15.4f}".format(name, func(val_probs), func(test_probs)))

# 3. Confidence breakdown
print("\n3. PREDICTION CONFIDENCE BREAKDOWN")
bins = [(0, 0.1, 'Very low risk (<10%)'),
        (0.1, 0.3, 'Low risk (10-30%)'),
        (0.3, 0.5, 'Moderate risk (30-50%)'),
        (0.5, 0.7, 'Elevated risk (50-70%)'),
        (0.7, 0.9, 'High risk (70-90%)'),
        (0.9, 1.01, 'Very high risk (>90%)')]
print("   {:<25} {:>15} {:>15}".format("Risk bucket", "Internal Val", "Comp. Test"))
print("   {} {} {}".format("-" * 25, "-" * 15, "-" * 15))
for lo, hi, label in bins:
    v = ((val_probs >= lo) & (val_probs < hi)).mean()
    t = ((test_probs >= lo) & (test_probs < hi)).mean()
    print("   {:<25} {:>14.1%} {:>14.1%}".format(label, v, t))

# 4. Key feature distributions
print("\n4. KEY FEATURE DISTRIBUTIONS (mean values)")
key_feats = ['age', 'a1c_latest', 'a1c_mean', 'n_a1c_tests', 'total_med_classes',
             'a1c_above_9', 'on_insulin', 'no_medication', 'any_admission']
print("   {:<25} {:>15} {:>15} {:>10}".format("Feature", "Internal Val", "Comp. Test", "Diff"))
print("   {} {} {} {}".format("-" * 25, "-" * 15, "-" * 15, "-" * 10))
for feat in key_feats:
    v = X_val_aligned[feat].mean()
    t = test[feat].mean()
    diff_pct = (t - v) / v * 100 if v != 0 else 0
    flag = ' !!' if abs(diff_pct) > 15 else ''
    print("   {:<25} {:>15.3f} {:>15.3f} {:>+9.1f}%{}".format(feat, v, t, diff_pct, flag))

# 5. Internal validation performance (reference)
val_auc = roc_auc_score(y_val, val_probs)
print("\n5. INTERNAL VALIDATION PERFORMANCE (reference)")
print("   AUC-ROC on 20% holdout: {:.4f}".format(val_auc))
print("   (Cannot compute AUC on competition test set -- no labels)")

# ══════════════════════════════════════════════════════════════════════════════
# PLOTS
# ══════════════════════════════════════════════════════════════════════════════

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Competition Test Set vs Internal Validation (threshold = {})'.format(THRESHOLD),
             fontsize=14, fontweight='bold')

# Plot 1: Probability distributions overlay
ax = axes[0, 0]
ax.hist(val_probs, bins=50, alpha=0.6, density=True,
        label='Internal val (n={:,})'.format(len(val_probs)), color='#4C72B0')
ax.hist(test_probs, bins=50, alpha=0.6, density=True,
        label='Comp. test (n={:,})'.format(len(test_probs)), color='#DD8452')
ax.axvline(THRESHOLD, color='red', linestyle='--', alpha=0.7, label='Threshold ({})'.format(THRESHOLD))
ax.set_xlabel('Predicted probability of uncontrolled A1c')
ax.set_ylabel('Density')
ax.set_title('Predicted Probability Distributions')
ax.legend()

# Plot 2: Cumulative distribution
ax = axes[0, 1]
val_sorted = np.sort(val_probs)
test_sorted = np.sort(test_probs)
ax.plot(val_sorted, np.linspace(0, 1, len(val_sorted)), label='Internal val', color='#4C72B0')
ax.plot(test_sorted, np.linspace(0, 1, len(test_sorted)), label='Comp. test', color='#DD8452')
ax.axvline(THRESHOLD, color='red', linestyle='--', alpha=0.7, label='Threshold ({})'.format(THRESHOLD))
ax.set_xlabel('Predicted probability')
ax.set_ylabel('Cumulative proportion')
ax.set_title('Cumulative Distribution (CDF)')
ax.legend()

# Plot 3: Confidence bucket comparison
ax = axes[1, 0]
labels = [b[2] for b in bins]
val_counts = [((val_probs >= lo) & (val_probs < hi)).mean() for lo, hi, _ in bins]
test_counts = [((test_probs >= lo) & (test_probs < hi)).mean() for lo, hi, _ in bins]
x = np.arange(len(labels))
w = 0.35
ax.barh(x - w/2, val_counts, w, label='Internal val', color='#4C72B0')
ax.barh(x + w/2, test_counts, w, label='Comp. test', color='#DD8452')
ax.set_yticks(x)
ax.set_yticklabels([l.split('(')[0].strip() for l in labels], fontsize=9)
ax.set_xlabel('Proportion of patients')
ax.set_title('Risk Bucket Distribution')
ax.legend()

# Plot 4: Key feature comparison
ax = axes[1, 1]
val_means = [X_val_aligned[f].mean() for f in key_feats]
test_means = [test[f].mean() for f in key_feats]
ratios = [t/v if v != 0 else 1 for v, t in zip(val_means, test_means)]
colors = ['#C44E52' if abs(r - 1) > 0.15 else '#4C72B0' for r in ratios]
ax.barh(range(len(key_feats)), ratios, color=colors)
ax.set_yticks(range(len(key_feats)))
ax.set_yticklabels(key_feats, fontsize=9)
ax.axvline(1.0, color='black', linestyle='--', alpha=0.5)
ax.set_xlabel('Comp. Test / Internal Val ratio (1.0 = identical)')
ax.set_title('Feature Mean Comparison')
ax.set_xlim(0.5, 1.5)

plt.tight_layout()
plt.savefig('plots/final_test_vs_val_comparison.png', dpi=150, bbox_inches='tight')
print('\nSaved: plots/final_test_vs_val_comparison.png')

# ══════════════════════════════════════════════════════════════════════════════
# GENERATE SUBMISSION
# ══════════════════════════════════════════════════════════════════════════════

submission = pd.DataFrame({
    'a1c 2025 Uncontrolled': test_preds
}, index=test.index)
submission.to_csv('submission/final_submission.csv')

detailed = pd.DataFrame({
    'predicted_probability': test_probs,
    'predicted_uncontrolled': test_preds,
}, index=test.index)
detailed.to_csv('submission/final_submission_detailed.csv')

print("\n" + "=" * 70)
print("SUBMISSION GENERATED")
print("=" * 70)
print("  File: submission/final_submission.csv")
print("  Patients: {:,}".format(len(submission)))
print("  Predicted uncontrolled: {:,} ({:.1%})".format(test_preds.sum(), test_rate))
print("  Predicted controlled:   {:,} ({:.1%})".format((~test_preds).sum(), 1 - test_rate))
print("  Threshold: {} (sensitivity-prioritized for clinical screening)".format(THRESHOLD))
print("  Model: XGBoost trained on 100% of training data (62,425 patients)")
print("  Internal validation AUC: {:.4f}".format(val_auc))
