"""
Build all figures and the Tableau export for the cv-risk-gaps portfolio project.

Reads from:
  ../../nhanes-cancer-survival/analysis/cv_risk_gaps/   (model outputs)
  ../../nhanes-cancer-survival/data/analytic_cohort_cv.csv (raw cohort)

Writes to:
  ../figures/    (3 portfolio figures + 1 card image, 300 DPI, dark theme)
  ../data/tableau_export.csv
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

PROJECT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT.parent / 'nhanes-cancer-survival'
SOURCE_ANALYSIS = SOURCE_DIR / 'analysis' / 'cv_risk_gaps'
SOURCE_DATA = SOURCE_DIR / 'data' / 'analytic_cohort_cv.csv'

FIG_DIR = PROJECT / 'figures'
DATA_DIR = PROJECT / 'data'
FIG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Dark portfolio palette
BG = '#0F0D2A'
BG_PANEL = '#1A1540'
TEXT = '#E0E7FF'
MUTED = '#A5B4FC'
ACCENT = '#818CF8'
ACCENT_BRIGHT = '#A5B4FC'
PINK = '#F472B6'
GREEN = '#34D399'
GRID = '#312E81'

mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Plus Jakarta Sans', 'Helvetica Neue', 'Arial', 'sans-serif'],
    'axes.edgecolor': MUTED,
    'axes.labelcolor': TEXT,
    'xtick.color': MUTED,
    'ytick.color': MUTED,
    'text.color': TEXT,
    'figure.facecolor': BG,
    'axes.facecolor': BG,
    'savefig.facecolor': BG,
    'savefig.edgecolor': BG,
})


def style_axes(ax):
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)
    for s in ['left', 'bottom']:
        ax.spines[s].set_color(MUTED)
        ax.spines[s].set_linewidth(0.8)
    ax.grid(axis='x', color=GRID, alpha=0.4, linewidth=0.6)
    ax.tick_params(colors=MUTED, length=0)


# =========================================================================
# Figure 1: Forest plot of cancer effect across 3 outcomes
# =========================================================================
def fig_forest():
    fr = pd.read_csv(SOURCE_ANALYSIS / 'forest_data.csv')
    # Order: BP, A1c, Cholesterol (top to bottom)
    order = ['bp_controlled', 'a1c_controlled', 'chol_high']
    labels_map = {
        'bp_controlled':  'BP control\nhypertensives',
        'a1c_controlled': 'A1c control\ndiabetics',
        'chol_high':      'High cholesterol\nfull sample',
    }
    fr = fr.set_index('key').loc[order].reset_index()
    fr['label'] = fr['key'].map(labels_map)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    y = np.arange(len(fr))[::-1]
    xerr_lo = fr['OR'].values - fr['CI_lo'].values
    xerr_hi = fr['CI_hi'].values - fr['OR'].values

    colors = [ACCENT, PINK, GREEN]
    for i, (yi, row, c) in enumerate(zip(y, fr.itertuples(), colors)):
        ax.errorbar(row.OR, yi,
                    xerr=[[xerr_lo[i]], [xerr_hi[i]]],
                    fmt='o', color=c, ecolor=c, alpha=0.95,
                    capsize=6, lw=2.2, markersize=14,
                    markeredgecolor=BG, markeredgewidth=2)
        ax.text(row.CI_hi * 1.06, yi,
                f'OR {row.OR:.2f}  ({row.CI_lo:.2f}, {row.CI_hi:.2f})',
                va='center', ha='left', fontsize=11, color=TEXT, fontweight='600')

    ax.axvline(1, color=MUTED, linestyle='--', lw=1.2, alpha=0.6, zorder=0)
    ax.set_yticks(y)
    ax.set_yticklabels(fr['label'], fontsize=12, color=TEXT)
    ax.set_xlabel('Adjusted Odds Ratio (cancer survivor vs non-cancer)',
                  fontsize=11, color=MUTED, labelpad=10)
    ax.set_xscale('log')
    ax.set_xlim(0.5, 3.0)
    ax.set_xticks([0.6, 0.8, 1.0, 1.5, 2.0])
    ax.set_xticklabels(['0.6', '0.8', '1.0', '1.5', '2.0'])
    ax.set_title('Cardiovascular care gaps in cancer survivors',
                 fontsize=15, color=TEXT, pad=18, fontweight='700', loc='left')
    style_axes(ax)
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'forest_cancer_effect.png', dpi=300, bbox_inches='tight')
    plt.close()
    return fr


# =========================================================================
# Figure 2: Grouped bar chart % controlled by cancer status
# =========================================================================
def fig_bars():
    df = pd.read_csv(SOURCE_DATA)
    df['depressed'] = df['depressed'].map({'True': 1, 'False': 0, True: 1, False: 0})

    def w_prop(sub, col):
        m = sub[col].notna()
        if not m.any():
            return np.nan
        w = sub.loc[m, 'wt_pooled'].values
        return float(np.sum(w * sub.loc[m, col].astype(float).values) / np.sum(w))

    bp_htn = df[df['hypertension'] == 1]
    dm = df[df['diabetes'] == 1]
    rows = [
        ('BP controlled\n(hypertensives)',
         w_prop(bp_htn[bp_htn['cancer'] == 0], 'bp_controlled'),
         w_prop(bp_htn[bp_htn['cancer'] == 1], 'bp_controlled')),
        ('A1c controlled\n(diabetics)',
         w_prop(dm[dm['cancer'] == 0], 'a1c_controlled'),
         w_prop(dm[dm['cancer'] == 1], 'a1c_controlled')),
        ('Total chol \u2265240\n(full sample)',
         w_prop(df[df['cancer'] == 0], 'chol_high'),
         w_prop(df[df['cancer'] == 1], 'chol_high')),
    ]
    bars = pd.DataFrame(rows, columns=['outcome', 'non_cancer', 'cancer'])

    fig, ax = plt.subplots(figsize=(9, 5.0))
    x = np.arange(len(bars))
    w = 0.36
    b1 = ax.bar(x - w / 2, bars['non_cancer'] * 100, w,
                label='Non-cancer', color=MUTED, alpha=0.95,
                edgecolor=BG, linewidth=1.5)
    b2 = ax.bar(x + w / 2, bars['cancer'] * 100, w,
                label='Cancer survivor', color=ACCENT, alpha=0.95,
                edgecolor=BG, linewidth=1.5)

    for bars_set in [b1, b2]:
        for rect in bars_set:
            h = rect.get_height()
            ax.text(rect.get_x() + rect.get_width() / 2, h + 1.2,
                    f'{h:.0f}%', ha='center', va='bottom',
                    fontsize=11, color=TEXT, fontweight='600')

    ax.set_xticks(x)
    ax.set_xticklabels(bars['outcome'], fontsize=11, color=TEXT)
    ax.set_ylabel('Survey-weighted prevalence (%)', fontsize=11, color=MUTED, labelpad=10)
    ax.set_ylim(0, max(bars[['non_cancer', 'cancer']].max()) * 100 * 1.25)
    ax.set_title('Cancer survivors do better at BP and A1c control',
                 fontsize=15, color=TEXT, pad=18, fontweight='700', loc='left')
    leg = ax.legend(loc='upper right', frameon=False, fontsize=11,
                    labelcolor=TEXT)
    style_axes(ax)
    ax.grid(axis='y', color=GRID, alpha=0.4, linewidth=0.6)
    ax.grid(axis='x', visible=False)
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'control_rates_by_cancer.png', dpi=300, bbox_inches='tight')
    plt.close()
    return bars


# =========================================================================
# Figure 3: BP control OR trend across NHANES cycles
# =========================================================================
def fig_trend():
    tr = pd.read_csv(SOURCE_ANALYSIS / 'cycle_trends_bp_controlled.csv')
    tr = tr.sort_values('cycle').reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(9, 5.0))
    x = np.arange(len(tr))
    ax.fill_between(x, tr['CI_lo'], tr['CI_hi'],
                    color=ACCENT, alpha=0.18, linewidth=0)
    ax.plot(x, tr['OR'], color=ACCENT_BRIGHT, lw=2.4, marker='o',
            markersize=10, markeredgecolor=BG, markeredgewidth=2,
            markerfacecolor=ACCENT_BRIGHT)
    ax.axhline(1, color=MUTED, linestyle='--', lw=1.2, alpha=0.6, zorder=0)

    for i, row in tr.iterrows():
        ax.text(i, row['OR'] + 0.07, f'{row["OR"]:.2f}',
                ha='center', va='bottom', fontsize=10,
                color=TEXT, fontweight='600')

    ax.set_xticks(x)
    ax.set_xticklabels(tr['cycle'], fontsize=10, color=MUTED, rotation=0)
    ax.set_ylabel('Adjusted OR (cancer vs non-cancer)',
                  fontsize=11, color=MUTED, labelpad=10)
    ax.set_title('Cancer survivors have consistently better BP control across cycles',
                 fontsize=14, color=TEXT, pad=18, fontweight='700', loc='left')
    ax.set_ylim(0.5, max(tr['CI_hi'].max() * 1.1, 2.0))
    style_axes(ax)
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'trend_bp_control_by_cycle.png', dpi=300, bbox_inches='tight')
    plt.close()
    return tr


# =========================================================================
# Figure 4: Portfolio card image (hero stat + mini forest)
# =========================================================================
def fig_card():
    fr = pd.read_csv(SOURCE_ANALYSIS / 'forest_data.csv')
    fr = fr.set_index('key').loc[['bp_controlled', 'a1c_controlled', 'chol_high']].reset_index()

    fig = plt.figure(figsize=(10, 6.25), facecolor=BG)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.15], wspace=0.05,
                          left=0.06, right=0.96, top=0.88, bottom=0.12)

    # Left panel: hero stat
    axL = fig.add_subplot(gs[0, 0])
    axL.set_facecolor(BG)
    axL.axis('off')
    axL.text(0, 0.85, 'OR 1.26', fontsize=66, color=ACCENT_BRIGHT,
             fontweight='800', va='top', ha='left')
    axL.text(0, 0.55, 'Cancer survivors with\nhypertension are 26% more\nlikely to have controlled BP',
             fontsize=14, color=TEXT, va='top', ha='left',
             linespacing=1.45, fontweight='500')
    axL.text(0, 0.16, 'NHANES 1999\u20132018 \u00b7 n = 11,772',
             fontsize=11, color=MUTED, va='top', ha='left', fontweight='500')
    axL.set_xlim(0, 1)
    axL.set_ylim(0, 1)

    # Right panel: mini forest
    axR = fig.add_subplot(gs[0, 1])
    axR.set_facecolor(BG)
    labels_map = {
        'bp_controlled':  'BP control',
        'a1c_controlled': 'A1c control',
        'chol_high':      'High cholesterol',
    }
    fr['label'] = fr['key'].map(labels_map)
    y = np.arange(len(fr))[::-1]
    xerr_lo = fr['OR'].values - fr['CI_lo'].values
    xerr_hi = fr['CI_hi'].values - fr['OR'].values
    colors = [ACCENT_BRIGHT, PINK, GREEN]
    for i, (yi, row, c) in enumerate(zip(y, fr.itertuples(), colors)):
        axR.errorbar(row.OR, yi, xerr=[[xerr_lo[i]], [xerr_hi[i]]],
                     fmt='o', color=c, ecolor=c, alpha=0.95,
                     capsize=5, lw=2, markersize=11,
                     markeredgecolor=BG, markeredgewidth=2)
        axR.text(row.CI_hi * 1.07, yi, f'{row.OR:.2f}',
                 va='center', ha='left', fontsize=11, color=TEXT, fontweight='600')
    axR.axvline(1, color=MUTED, linestyle='--', lw=1.2, alpha=0.5, zorder=0)
    axR.set_yticks(y)
    axR.set_yticklabels(fr['label'], fontsize=11, color=TEXT)
    axR.set_xlabel('Adjusted OR', fontsize=10, color=MUTED, labelpad=8)
    axR.set_xscale('log')
    axR.set_xlim(0.55, 2.5)
    axR.set_xticks([0.7, 1.0, 1.5, 2.0])
    axR.set_xticklabels(['0.7', '1.0', '1.5', '2.0'])
    style_axes(axR)
    axR.grid(axis='x', color=GRID, alpha=0.4, linewidth=0.6)

    # Title bar
    fig.text(0.06, 0.94, 'C A R D I O V A S C U L A R   R I S K   I N   C A N C E R   S U R V I V O R S',
             fontsize=11, color=ACCENT, fontweight='700')

    plt.savefig(FIG_DIR / 'card_cv_risk_gaps.png', dpi=300, bbox_inches='tight',
                facecolor=BG)
    plt.close()


# =========================================================================
# Tableau export
# =========================================================================
def make_tableau_export():
    df = pd.read_csv(SOURCE_DATA)
    df['depressed'] = df['depressed'].map({'True': 1, 'False': 0, True: 1, False: 0})
    cols = [
        'cancer', 'age_group', 'female', 'race_ethnicity', 'cycle',
        'hypertension', 'diabetes', 'bp_controlled', 'a1c_controlled',
        'chol_high', 'depressed', 'phq9_severity', 'on_bp_meds',
        'on_chol_meds', 'wt_pooled',
    ]
    out = df[cols].copy()
    out['cancer'] = out['cancer'].map({1: 'Cancer survivor', 0: 'Non-cancer'})
    out['female'] = out['female'].map({1: 'Female', 0: 'Male'})
    out = out.rename(columns={
        'cancer': 'cancer_status',
        'female': 'sex',
        'wt_pooled': 'survey_weight',
    })
    out.to_csv(DATA_DIR / 'tableau_export.csv', index=False)
    return len(out), len(out.columns)


def main():
    print('Generating figures and exports for cv-risk-gaps project')
    print('=' * 60)
    fr = fig_forest()
    print(f'  forest_cancer_effect.png  ({len(fr)} outcomes)')
    bars = fig_bars()
    print(f'  control_rates_by_cancer.png  ({len(bars)} groups)')
    tr = fig_trend()
    print(f'  trend_bp_control_by_cycle.png  ({len(tr)} cycles)')
    fig_card()
    print('  card_cv_risk_gaps.png  (portfolio card)')
    n, c = make_tableau_export()
    print(f'\nTableau export: {n:,} rows x {c} cols')
    print(f'\nAll outputs in: {FIG_DIR.parent}')


if __name__ == '__main__':
    main()
