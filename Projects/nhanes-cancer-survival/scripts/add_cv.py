"""
Download NHANES BPX (blood pressure exam) and cholesterol lab files
(TCHOL for total cholesterol, TRIGLY for LDL) across cycles 1999-2018,
plus reuse the already-downloaded BPQ files for medication variables.
Merge into analytic_cohort_phq9.csv and derive 5 cardiovascular variables.

Output: data/analytic_cohort_cv.csv (analytic_cohort_phq9.csv preserved)

Variables created:
  bp_controlled  : 1 if mean SBP < 140 AND mean DBP < 90, among hypertensives
  a1c_controlled : 1 if LBXGH < 7.0, among diabetics
  chol_high      : 1 if total cholesterol >= 240 mg/dL
  on_bp_meds     : 1 if BPQ050A == 1 (currently taking BP medication)
  on_chol_meds   : 1 if BPQ100D == 1 (currently taking cholesterol medication)
"""

from pathlib import Path
from urllib.request import urlretrieve

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / 'data'
COHORT_IN = DATA / 'analytic_cohort_phq9.csv'
COHORT_OUT = DATA / 'analytic_cohort_cv.csv'

# cycle -> (start_year, BPX file, TCHOL file, TRIGLY file)
# File suffixes follow standard NHANES naming. Pre-2005 cycles used the
# older LAB13 / L13_B / L13_C names; from 2005-2006 onward CDC switched
# to TCHOL_x for total cholesterol and TRIGLY_x for triglycerides+LDL.
CYCLES = {
    '1999-2000': ('1999', 'BPX',   'LAB13',   'LAB13AM'),
    '2001-2002': ('2001', 'BPX_B', 'L13_B',   'L13AM_B'),
    '2003-2004': ('2003', 'BPX_C', 'L13_C',   'L13AM_C'),
    '2005-2006': ('2005', 'BPX_D', 'TCHOL_D', 'TRIGLY_D'),
    '2007-2008': ('2007', 'BPX_E', 'TCHOL_E', 'TRIGLY_E'),
    '2009-2010': ('2009', 'BPX_F', 'TCHOL_F', 'TRIGLY_F'),
    '2011-2012': ('2011', 'BPX_G', 'TCHOL_G', 'TRIGLY_G'),
    '2013-2014': ('2013', 'BPX_H', 'TCHOL_H', 'TRIGLY_H'),
    '2015-2016': ('2015', 'BPX_I', 'TCHOL_I', 'TRIGLY_I'),
    '2017-2018': ('2017', 'BPX_J', 'TCHOL_J', 'TRIGLY_J'),
}

SBP_COLS = ['BPXSY1', 'BPXSY2', 'BPXSY3', 'BPXSY4']
DBP_COLS = ['BPXDI1', 'BPXDI2', 'BPXDI3', 'BPXDI4']


def download_xpt(cycle: str, start_year: str, file_name: str, kind: str) -> Path:
    """Download one XPT file from CDC if not already present and valid."""
    local = DATA / f'{cycle}_{kind}.XPT'
    if local.exists() and local.stat().st_size > 1000 and not local.read_bytes()[:15].startswith(b'<!DOCTYPE'):
        print(f'  exists: {local.name}')
        return local
    url = f'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{start_year}/DataFiles/{file_name}.XPT'
    print(f'  downloading: {url}')
    try:
        urlretrieve(url, local)
        # Sanity check
        if local.read_bytes()[:15].startswith(b'<!DOCTYPE'):
            local.unlink()
            print(f'  WARNING: {file_name}.XPT returned HTML error page (file not on CDC)')
            return None
        return local
    except Exception as e:
        print(f'  FAILED: {file_name}.XPT -- {e}')
        if local.exists():
            local.unlink()
        return None


def safe_read(path):
    """Read XPT, normalize SEQN. Returns None on failure."""
    if path is None or not path.exists():
        return None
    try:
        df = pd.read_sas(path, format='xport')
        df['SEQN'] = df['SEQN'].astype('int64')
        return df
    except Exception as e:
        print(f'  read error {path.name}: {e}')
        return None


def load_bpx(cycle: str, path: Path) -> pd.DataFrame:
    """Mean SBP and DBP across the up-to-4 readings in BPX."""
    df = safe_read(path)
    if df is None:
        return pd.DataFrame(columns=['SEQN', 'cycle', 'sbp_mean', 'dbp_mean'])
    sbp = [c for c in SBP_COLS if c in df.columns]
    dbp = [c for c in DBP_COLS if c in df.columns]
    # NHANES SAS encodes 0 as 5.4e-79; treat zero/missing diastolic as
    # not measured rather than a valid reading.
    for c in dbp:
        df[c] = df[c].where(df[c].round() > 0)
    df['sbp_mean'] = df[sbp].mean(axis=1) if sbp else np.nan
    df['dbp_mean'] = df[dbp].mean(axis=1) if dbp else np.nan
    df['cycle'] = cycle
    return df[['SEQN', 'cycle', 'sbp_mean', 'dbp_mean']]


def load_tchol(cycle: str, path: Path) -> pd.DataFrame:
    """Total cholesterol (LBXTC, mg/dL)."""
    df = safe_read(path)
    if df is None or 'LBXTC' not in df.columns:
        return pd.DataFrame(columns=['SEQN', 'cycle', 'total_chol'])
    df['cycle'] = cycle
    return df[['SEQN', 'cycle', 'LBXTC']].rename(columns={'LBXTC': 'total_chol'})


def load_ldl(cycle: str, path: Path) -> pd.DataFrame:
    """LDL cholesterol (LBDLDL, mg/dL, fasting subsample only)."""
    df = safe_read(path)
    if df is None or 'LBDLDL' not in df.columns:
        return pd.DataFrame(columns=['SEQN', 'cycle', 'ldl_chol'])
    df['cycle'] = cycle
    return df[['SEQN', 'cycle', 'LBDLDL']].rename(columns={'LBDLDL': 'ldl_chol'})


def load_bpq(cycle: str, path: Path) -> pd.DataFrame:
    """Reuse the already-downloaded BPQ file for medication variables.
    BPQ050A: currently taking BP medication (1=yes, 2=no)
    BPQ100D: currently taking cholesterol medication (later cycles only)
    """
    df = safe_read(path)
    if df is None:
        return pd.DataFrame(columns=['SEQN', 'cycle', 'on_bp_meds', 'on_chol_meds'])
    df['cycle'] = cycle
    # Round to handle the SAS 0 = 5.4e-79 quirk
    if 'BPQ050A' in df.columns:
        bp_med = df['BPQ050A'].round()
        df['on_bp_meds'] = (bp_med == 1).astype('Int64').where(bp_med.isin([1, 2]))
    else:
        df['on_bp_meds'] = pd.NA
    if 'BPQ100D' in df.columns:
        chol_med = df['BPQ100D'].round()
        df['on_chol_meds'] = (chol_med == 1).astype('Int64').where(chol_med.isin([1, 2]))
    else:
        df['on_chol_meds'] = pd.NA
    return df[['SEQN', 'cycle', 'on_bp_meds', 'on_chol_meds']]


def main():
    bpx_frames, tc_frames, ldl_frames, bpq_frames = [], [], [], []

    for cycle, (year, bpx, tc, ldl) in CYCLES.items():
        print(f'\n{cycle}:')
        bpx_path = download_xpt(cycle, year, bpx, 'bpx')
        tc_path  = download_xpt(cycle, year, tc,  'tchol')
        ldl_path = download_xpt(cycle, year, ldl, 'trigly')
        bpq_path = DATA / f'{cycle}_bpq.XPT'
        if not bpq_path.exists():
            print(f'  WARNING: {bpq_path.name} missing (run download_data.py first)')

        bpx_frames.append(load_bpx(cycle, bpx_path))
        tc_frames.append(load_tchol(cycle, tc_path))
        ldl_frames.append(load_ldl(cycle, ldl_path))
        bpq_frames.append(load_bpq(cycle, bpq_path))

    bpx_all = pd.concat(bpx_frames, ignore_index=True)
    tc_all  = pd.concat(tc_frames,  ignore_index=True)
    ldl_all = pd.concat(ldl_frames, ignore_index=True)
    bpq_all = pd.concat(bpq_frames, ignore_index=True)

    print(f'\nBPX rows:   {len(bpx_all):,}  with valid SBP: {bpx_all["sbp_mean"].notna().sum():,}')
    print(f'TCHOL rows: {len(tc_all):,}  with LBXTC:     {tc_all["total_chol"].notna().sum():,}')
    print(f'LDL rows:   {len(ldl_all):,}  with LBDLDL:    {ldl_all["ldl_chol"].notna().sum():,}')
    print(f'BPQ rows:   {len(bpq_all):,}  with BP med Q:  {bpq_all["on_bp_meds"].notna().sum():,}'
          f'  with chol med Q: {bpq_all["on_chol_meds"].notna().sum():,}')

    print(f'\nLoading cohort: {COHORT_IN.name}')
    cohort = pd.read_csv(COHORT_IN)
    print(f'  rows: {len(cohort):,}  cols: {cohort.shape[1]}')

    merged = (cohort
              .merge(bpx_all, on=['SEQN', 'cycle'], how='left')
              .merge(tc_all,  on=['SEQN', 'cycle'], how='left')
              .merge(ldl_all, on=['SEQN', 'cycle'], how='left')
              .merge(bpq_all, on=['SEQN', 'cycle'], how='left'))

    # Derived variables ----------------------------------------------------
    # 1. bp_controlled (only meaningful among hypertensives)
    bp_ok = (merged['sbp_mean'] < 140) & (merged['dbp_mean'] < 90)
    merged['bp_controlled'] = (
        bp_ok.astype('Int64')
        .where(merged['hypertension'] == 1)
        .where(merged['sbp_mean'].notna() & merged['dbp_mean'].notna())
    )

    # 2. a1c_controlled (only among diabetics)
    a1c_ok = merged['LBXGH'] < 7.0
    merged['a1c_controlled'] = (
        a1c_ok.astype('Int64')
        .where(merged['diabetes'] == 1)
        .where(merged['LBXGH'].notna())
    )

    # 3. chol_high (anyone with LBXTC measured)
    merged['chol_high'] = (
        (merged['total_chol'] >= 240).astype('Int64')
        .where(merged['total_chol'].notna())
    )

    # 4 & 5: on_bp_meds, on_chol_meds already merged in from BPQ.

    # Coverage report ------------------------------------------------------
    print('\nDerived variable coverage (full cohort):')
    for v in ['sbp_mean', 'dbp_mean', 'total_chol', 'ldl_chol',
              'bp_controlled', 'a1c_controlled', 'chol_high',
              'on_bp_meds', 'on_chol_meds']:
        n = merged[v].notna().sum()
        print(f'  {v:18s}  n = {n:,}')

    print('\nAmong hypertensives, BP control:')
    htn = merged[merged['hypertension'] == 1]
    if len(htn):
        print(f'  controlled:   {int((htn["bp_controlled"] == 1).sum()):,}')
        print(f'  uncontrolled: {int((htn["bp_controlled"] == 0).sum()):,}')
        print(f'  on BP meds:   {int((htn["on_bp_meds"] == 1).sum()):,}')

    print('\nAmong diabetics, A1c control:')
    dm = merged[merged['diabetes'] == 1]
    if len(dm):
        print(f'  controlled (A1c<7):   {int((dm["a1c_controlled"] == 1).sum()):,}')
        print(f'  uncontrolled:         {int((dm["a1c_controlled"] == 0).sum()):,}')

    print(f'\nHigh cholesterol (>=240): {int((merged["chol_high"] == 1).sum()):,}')

    merged.to_csv(COHORT_OUT, index=False)
    print(f'\nSaved: {COHORT_OUT}')
    print(f'  rows: {len(merged):,}  cols: {merged.shape[1]}')


if __name__ == '__main__':
    main()
