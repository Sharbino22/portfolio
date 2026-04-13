"""
Download NHANES DPQ (PHQ-9 depression screener) files for cycles 2005-2018,
compute PHQ-9 scores and severity categories, and merge into the existing
analytic_cohort.csv.

Output: data/analytic_cohort_phq9.csv (original file preserved)
"""

from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / 'data'
COHORT_IN = DATA / 'analytic_cohort.csv'
COHORT_OUT = DATA / 'analytic_cohort_phq9.csv'

# DPQ files: cycle -> (start_year, file_name)
CYCLES = {
    '2005-2006': ('2005', 'DPQ_D'),
    '2007-2008': ('2007', 'DPQ_E'),
    '2009-2010': ('2009', 'DPQ_F'),
    '2011-2012': ('2011', 'DPQ_G'),
    '2013-2014': ('2013', 'DPQ_H'),
    '2015-2016': ('2015', 'DPQ_I'),
    '2017-2018': ('2017', 'DPQ_J'),
}

PHQ_ITEMS = ['DPQ010', 'DPQ020', 'DPQ030', 'DPQ040',
             'DPQ050', 'DPQ060', 'DPQ070', 'DPQ080', 'DPQ090']


def download_dpq(cycle: str, start_year: str, file_name: str) -> Path:
    """Download one DPQ XPT file from CDC if not already present."""
    local = DATA / f'{cycle}_dpq.XPT'
    if local.exists() and local.stat().st_size > 1000 and not local.read_bytes()[:15].startswith(b'<!DOCTYPE'):
        print(f'  exists: {local.name}')
        return local
    url = f'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{start_year}/DataFiles/{file_name}.XPT'
    print(f'  downloading: {url}')
    urlretrieve(url, local)
    return local


def load_cycle(cycle: str, path: Path) -> pd.DataFrame:
    """Load one cycle of DPQ, compute PHQ-9 score, attach cycle label."""
    df = pd.read_sas(path, format='xport')
    df['SEQN'] = df['SEQN'].astype('int64')
    df['cycle'] = cycle
    # PHQ-9 items: 0-3 valid, 7=refused, 9=don't know -> NaN.
    # NHANES encodes 0 as a tiny float (5.4e-79); round before filtering.
    for item in PHQ_ITEMS:
        rounded = df[item].round()
        df[item] = rounded.where(rounded.isin([0, 1, 2, 3]))
    # Total score requires all 9 items present
    df['phq9_total'] = df[PHQ_ITEMS].sum(axis=1, min_count=9)
    return df[['SEQN', 'cycle', 'phq9_total']]


def severity(score: float) -> str:
    if pd.isna(score):
        return pd.NA
    if score <= 4:
        return 'minimal'
    if score <= 9:
        return 'mild'
    if score <= 14:
        return 'moderate'
    if score <= 19:
        return 'moderately_severe'
    return 'severe'


def main():
    print('Downloading DPQ files:')
    frames = []
    for cycle, (start_year, file_name) in CYCLES.items():
        local = download_dpq(cycle, start_year, file_name)
        frames.append(load_cycle(cycle, local))
    dpq = pd.concat(frames, ignore_index=True)
    print(f'Total DPQ rows: {len(dpq):,}')
    print(f'Non-missing PHQ-9 scores: {dpq["phq9_total"].notna().sum():,}')

    print(f'\nLoading cohort: {COHORT_IN.name}')
    cohort = pd.read_csv(COHORT_IN)
    print(f'  rows: {len(cohort):,}')

    # Merge on SEQN + cycle (left join: keep all cohort rows)
    merged = cohort.merge(dpq, on=['SEQN', 'cycle'], how='left')

    # Severity category and binary depression
    merged['phq9_severity'] = merged['phq9_total'].apply(severity)
    merged['depressed'] = (merged['phq9_total'] >= 10).where(
        merged['phq9_total'].notna()
    )

    # Coverage report
    eligible = merged[merged['cycle'].isin(CYCLES.keys())]
    print('\nMerge coverage (cycles 2005-2018 only):')
    print(f'  cohort rows in eligible cycles: {len(eligible):,}')
    print(f'  with PHQ-9 score:               {eligible["phq9_total"].notna().sum():,}')
    print(f'  depressed (PHQ-9 >= 10):        {int(eligible["depressed"].sum()):,}')

    print('\nSeverity distribution (eligible cycles):')
    print(eligible['phq9_severity'].value_counts(dropna=False).to_string())

    merged.to_csv(COHORT_OUT, index=False)
    print(f'\nSaved: {COHORT_OUT}')
    print(f'  rows: {len(merged):,}  cols: {merged.shape[1]}')


if __name__ == '__main__':
    main()
