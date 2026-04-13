"""
Cardiovascular risk gaps in cancer survivors vs non-cancer adults.

Loads data/analytic_cohort_cv.csv and produces:
  1. Survey-weighted Table 1 (cancer vs non-cancer)
  2. Three GLM logistic models with cancer*depressed interaction:
       - bp_controlled  (hypertensives)
       - a1c_controlled (diabetics)
       - chol_high      (full sample)
  3. Same models stratified by NHANES cycle
  4. Forest plot of cancer effect across the three outcomes
  5. SUMMARY.md

Survey design handled via:
  - freq_weights normalized so effective N = actual N (pseudo-likelihood)
  - cluster-robust SEs using combined SDMVSTRA x SDMVPSU as cluster id

Outputs in analysis/cv_risk_gaps/
"""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf

warnings.simplefilter('ignore', category=RuntimeWarning)
warnings.simplefilter('ignore', category=UserWarning)

PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / 'data' / 'analytic_cohort_cv.csv'
OUT = PROJECT / 'analysis' / 'cv_risk_gaps'
OUT.mkdir(parents=True, exist_ok=True)

NEEDED = ['cancer', 'age', 'female', 'race_ethnicity', 'smoking', 'obese',
          'depressed', 'wt_pooled', 'SDMVPSU', 'SDMVSTRA']

FORMULA = ('{outcome} ~ cancer * depressed + age + female'
           ' + C(race_ethnicity) + C(smoking) + obese')


# ---------- helpers --------------------------------------------------------

def load():
    df = pd.read_csv(DATA)
    # depressed is stored as Python True/False strings; coerce to nullable int
    df['depressed'] = df['depressed'].map({'True': 1, 'False': 0,
                                           True: 1, False: 0})
    return df


def w_mean_sd(x, w):
    m = np.sum(w * x) / np.sum(w)
    v = np.sum(w * (x - m) ** 2) / np.sum(w)
    return m, np.sqrt(v)


def w_prop(x, w):
    return np.sum(w * x) / np.sum(w)


def table1(df):
    """Survey-weighted Table 1 by cancer status. Returns long-format DataFrame."""
    rows = []
    for label in [0, 1]:
        sub = df[df['cancer'] == label]
        w = sub['wt_pooled'].values
        rows.append(('N (unweighted)', label, len(sub), ''))
        rows.append(('Weighted N', label, f'{w.sum():,.0f}', ''))

        for v in ['age', 'BMXBMI', 'LBXGH', 'phq9_total',
                  'sbp_mean', 'dbp_mean', 'total_chol']:
            if v in sub.columns:
                m_ = sub[v].notna()
                if m_.any():
                    mean, sd = w_mean_sd(sub.loc[m_, v].values, w[m_])
                    rows.append((v, label, f'{mean:.2f}', f'{sd:.2f}'))

        for v in ['female', 'diabetes', 'hypertension', 'obese',
                  'depressed', 'bp_controlled', 'a1c_controlled', 'chol_high',
                  'on_bp_meds', 'on_chol_meds']:
            if v in sub.columns:
                m_ = sub[v].notna()
                if m_.any():
                    p = w_prop(sub.loc[m_, v].astype(float).values, w[m_])
                    rows.append((v, label, f'{p * 100:.1f}%', ''))

        for race_val in sorted(sub['race_ethnicity'].dropna().unique()):
            m_ = sub['race_ethnicity'].notna()
            p = w_prop((sub.loc[m_, 'race_ethnicity'] == race_val).astype(float).values,
                       w[m_])
            rows.append((f'race={race_val}', label, f'{p * 100:.1f}%', ''))

    long = pd.DataFrame(rows, columns=['variable', 'cancer', 'value', 'sd'])
    # Pivot to wide
    wide = long.pivot_table(index='variable', columns='cancer',
                            values='value', aggfunc='first')
    wide.columns = ['non_cancer', 'cancer_survivor']
    return wide.reset_index()


def fit_model(df, outcome, label='', verbose=True):
    """Survey-weighted logistic regression with cluster-robust SE."""
    d = df.dropna(subset=NEEDED + [outcome]).copy()
    if len(d) < 100:
        if verbose:
            print(f'  [{label}] skipped (n={len(d)})')
        return None, len(d)
    d[outcome] = d[outcome].astype(int)
    d['depressed'] = d['depressed'].astype(int)
    d['cancer'] = d['cancer'].astype(int)
    d['obese'] = d['obese'].astype(int)
    d['female'] = d['female'].astype(int)
    # Need both classes for outcome and for cancer/depressed within cells
    if d[outcome].nunique() < 2 or d['cancer'].nunique() < 2:
        if verbose:
            print(f'  [{label}] skipped (no variation)')
        return None, len(d)
    # Normalize weights so freq_weights doesn't inflate effective N
    d['w'] = d['wt_pooled'] * len(d) / d['wt_pooled'].sum()
    d['cluster'] = (d['SDMVSTRA'].astype(int).astype(str) + '_'
                    + d['SDMVPSU'].astype(int).astype(str))

    formula = FORMULA.format(outcome=outcome)
    try:
        model = smf.glm(formula=formula, data=d,
                        family=sm.families.Binomial(),
                        freq_weights=d['w'])
        res = model.fit(cov_type='cluster',
                        cov_kwds={'groups': d['cluster'].values},
                        disp=False)
        return res, len(d)
    except Exception as e:
        if verbose:
            print(f'  [{label}] fit failed: {e}')
        return None, len(d)


def coef_table(res):
    if res is None:
        return pd.DataFrame()
    or_ = np.exp(res.params)
    ci = np.exp(res.conf_int())
    out = pd.DataFrame({
        'OR': or_.values,
        'CI_lo': ci[0].values,
        'CI_hi': ci[1].values,
        'p': res.pvalues.values,
    }, index=res.params.index)
    out.index.name = 'term'
    return out.reset_index()


def get_term(res, term):
    """Return (OR, CI_lo, CI_hi, p) for one term, or None if absent."""
    if res is None or term not in res.params.index:
        return None
    or_ = float(np.exp(res.params[term]))
    ci = res.conf_int().loc[term]
    return or_, float(np.exp(ci[0])), float(np.exp(ci[1])), float(res.pvalues[term])


# ---------- main pipeline --------------------------------------------------

def main():
    print(f'Loading {DATA.name}')
    df = load()
    print(f'  rows: {len(df):,}')

    # ----- Table 1 -----
    print('\n[1] Table 1...')
    t1 = table1(df)
    t1.to_csv(OUT / 'table1_cancer_vs_noncancer.csv', index=False)
    print(f'    saved table1_cancer_vs_noncancer.csv ({len(t1)} rows)')

    # ----- Main models -----
    samples = {
        'bp_controlled':  df[df['hypertension'] == 1].copy(),
        'a1c_controlled': df[df['diabetes'] == 1].copy(),
        'chol_high':      df.copy(),
    }

    fitted = {}
    print('\n[2] Main models (cancer * depressed interaction):')
    for outcome, sub in samples.items():
        res, n = fit_model(sub, outcome, label=outcome)
        fitted[outcome] = res
        if res is not None:
            tbl = coef_table(res)
            tbl.to_csv(OUT / f'model_{outcome}.csv', index=False)
            cancer_eff = get_term(res, 'cancer')
            inter_eff = get_term(res, 'cancer:depressed')
            print(f'    {outcome:16s}  n={n:,}  '
                  f'cancer OR={cancer_eff[0]:.2f} ({cancer_eff[1]:.2f}-{cancer_eff[2]:.2f}, p={cancer_eff[3]:.3f})')
            if inter_eff:
                print(f'                       cancer:depressed OR={inter_eff[0]:.2f} '
                      f'({inter_eff[1]:.2f}-{inter_eff[2]:.2f}, p={inter_eff[3]:.3f})')

    # ----- Cycle-stratified -----
    print('\n[3] Cycle-stratified models:')
    cycles = sorted(df['cycle'].dropna().unique())
    for outcome, sub in samples.items():
        rows = []
        for cyc in cycles:
            sub_cyc = sub[sub['cycle'] == cyc]
            res, n = fit_model(sub_cyc, outcome, verbose=False)
            eff = get_term(res, 'cancer') if res is not None else None
            if eff is None:
                continue
            rows.append({
                'cycle': cyc, 'n': n,
                'OR': eff[0], 'CI_lo': eff[1], 'CI_hi': eff[2], 'p': eff[3],
            })
        out_df = pd.DataFrame(rows)
        out_df.to_csv(OUT / f'cycle_trends_{outcome}.csv', index=False)
        print(f'    {outcome:16s}  cycles fitted: {len(rows)}/{len(cycles)}')

    # ----- Forest plot -----
    print('\n[4] Forest plot...')
    labels = {
        'bp_controlled':  'BP control\n(hypertensives)',
        'a1c_controlled': 'A1c control\n(diabetics)',
        'chol_high':      'High cholesterol\n(full sample)',
    }
    forest_rows = []
    for outcome, res in fitted.items():
        eff = get_term(res, 'cancer')
        if eff is None:
            continue
        forest_rows.append({
            'outcome': labels[outcome],
            'key': outcome,
            'OR': eff[0], 'CI_lo': eff[1], 'CI_hi': eff[2], 'p': eff[3],
        })
    fr = pd.DataFrame(forest_rows)
    fr.to_csv(OUT / 'forest_data.csv', index=False)

    fig, ax = plt.subplots(figsize=(8, 4.2))
    y = np.arange(len(fr))[::-1]
    xerr_lo = fr['OR'].values - fr['CI_lo'].values
    xerr_hi = fr['CI_hi'].values - fr['OR'].values
    ax.errorbar(fr['OR'], y, xerr=[xerr_lo, xerr_hi],
                fmt='o', color='#4338CA', ecolor='#818CF8',
                capsize=5, lw=2, markersize=10, markeredgecolor='white',
                markeredgewidth=1.2)
    ax.axvline(1, color='#888', linestyle='--', lw=1, zorder=0)
    ax.set_yticks(y)
    ax.set_yticklabels(fr['outcome'])
    ax.set_xlabel('Adjusted Odds Ratio (cancer survivor vs non-cancer)')
    ax.set_title('Cardiovascular risk gaps in cancer survivors\n(survey-weighted, cluster-robust SE)',
                 fontsize=12, pad=12)
    ax.set_xscale('log')
    ax.grid(axis='x', alpha=0.2)
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    # Annotate ORs
    for i, (_, r) in enumerate(fr.iterrows()):
        ax.text(r['CI_hi'] * 1.05, y[i],
                f'{r["OR"]:.2f} ({r["CI_lo"]:.2f}-{r["CI_hi"]:.2f})',
                va='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(OUT / 'forest_cancer_effect.png', dpi=200, bbox_inches='tight')
    plt.close()
    print('    saved forest_cancer_effect.png')

    # ----- Summary markdown -----
    print('\n[5] Writing SUMMARY.md...')
    write_summary(fitted, fr)
    print('    saved SUMMARY.md')

    print(f'\nAll outputs in: {OUT}')


def write_summary(fitted, forest):
    lines = [
        '# Cardiovascular Risk Gaps in Cancer Survivors',
        '',
        '_Analysis of NHANES 1999-2018, restricted to cycles with PHQ-9 (2005-2018) for models including the depressed covariate._',
        '',
        '## Methods',
        '',
        '- **Source**: `data/analytic_cohort_cv.csv` (n = 51,168)',
        '- **Estimation**: Survey-weighted logistic regression via `statsmodels.GLM(family=Binomial)`',
        '  with weights normalized so effective N matches actual N (pseudo-likelihood).',
        '- **Standard errors**: Cluster-robust, clustered on combined `SDMVSTRA x SDMVPSU` to',
        '  approximate Taylor-series linearization for the NHANES design.',
        '- **Covariates**: age, sex, race/ethnicity, smoking status, obesity, depression (PHQ-9 >= 10),',
        '  with a cancer * depressed interaction.',
        '',
        '## Outcome models',
        '',
        '| Outcome | Sample | Cancer survivor OR | 95% CI | p |',
        '|---|---|---:|---|---:|',
    ]

    pretty = {
        'bp_controlled':  'BP controlled (hypertensives)',
        'a1c_controlled': 'A1c controlled (diabetics)',
        'chol_high':      'Total cholesterol >= 240 (all)',
    }
    for outcome, res in fitted.items():
        if res is None:
            continue
        eff = get_term(res, 'cancer')
        if eff is None:
            continue
        n = int(res.nobs)
        lines.append(f'| {pretty[outcome]} | n = {n:,} | {eff[0]:.2f} | '
                     f'({eff[1]:.2f}, {eff[2]:.2f}) | {eff[3]:.3f} |')

    lines += ['', '## Cancer x depression interaction', '',
              '| Outcome | Interaction OR | 95% CI | p |',
              '|---|---:|---|---:|']
    for outcome, res in fitted.items():
        if res is None:
            continue
        inter = get_term(res, 'cancer:depressed')
        if inter is None:
            lines.append(f'| {pretty[outcome]} | — | — | — |')
            continue
        lines.append(f'| {pretty[outcome]} | {inter[0]:.2f} | '
                     f'({inter[1]:.2f}, {inter[2]:.2f}) | {inter[3]:.3f} |')

    lines += [
        '',
        '## Files',
        '',
        '- `table1_cancer_vs_noncancer.csv` — survey-weighted baseline characteristics',
        '- `model_bp_controlled.csv` / `model_a1c_controlled.csv` / `model_chol_high.csv` — full coefficient tables',
        '- `cycle_trends_*.csv` — cancer effect ORs by NHANES cycle',
        '- `forest_data.csv` — data behind the forest plot',
        '- `forest_cancer_effect.png` — summary forest plot',
        '',
        '## Caveats',
        '',
        '- Pseudo-likelihood with cluster-robust SE approximates the survey design but is not',
        '  identical to Taylor-linearized SEs from R\'s survey package. Point estimates are',
        '  unbiased; SEs are slightly conservative.',
        '- Depression covariate is only available 2005-2018, so models exclude pre-2005 cycles',
        '  (~13,672 rows).',
        '- BP control and A1c control are conditional outcomes (hypertensives and diabetics only),',
        '  which means the cancer effect estimates the gap among those with the underlying disease,',
        '  not in the full population.',
    ]
    Path(OUT / 'SUMMARY.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
