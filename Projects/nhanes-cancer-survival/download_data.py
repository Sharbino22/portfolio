"""
NHANES Data Downloader for Cancer Survivorship & Mortality Project
=================================================================
Downloads all required NHANES survey files (1999-2018) and linked mortality data from CDC.
Uses curl and the current CDC URL format (as of 2025).

Usage:
    python3 download_data.py

All files are saved to the 'data/' subfolder.
Total download size: approximately 150-200 MB.
"""

import subprocess
import os
import sys


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# New CDC URL format: /Nchs/Data/Nhanes/Public/{START_YEAR}/DataFiles/{TABLE}.XPT
NHANES_BASE = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public"

# ---------------------------------------------------------------
# 10 NHANES cycles: (cycle_label, start_year, suffix)
# ---------------------------------------------------------------
CYCLES = [
    ("1999-2000", "1999", ""),
    ("2001-2002", "2001", "_B"),
    ("2003-2004", "2003", "_C"),
    ("2005-2006", "2005", "_D"),
    ("2007-2008", "2007", "_E"),
    ("2009-2010", "2009", "_F"),
    ("2011-2012", "2011", "_G"),
    ("2013-2014", "2013", "_H"),
    ("2015-2016", "2015", "_I"),
    ("2017-2018", "2017", "_J"),
]

# ---------------------------------------------------------------
# Survey components needed for this analysis
# ---------------------------------------------------------------
STANDARD_COMPONENTS = {
    "demo": "DEMO",       # Demographics (age, sex, race, education)
    "mcq": "MCQ",         # Medical conditions (cancer history)
    "diq": "DIQ",         # Diabetes questionnaire
    "bmx": "BMX",         # Body measures (BMI)
    "bpq": "BPQ",         # Blood pressure questionnaire (hypertension)
    "smq": "SMQ",         # Smoking questionnaire
}

# HbA1c files (inconsistent naming across early cycles)
HBA1C_FILES = {
    "1999-2000": "LAB10",
    "2001-2002": "L10_B",
    "2003-2004": "L10_C",
    "2005-2006": "GHB_D",
    "2007-2008": "GHB_E",
    "2009-2010": "GHB_F",
    "2011-2012": "GHB_G",
    "2013-2014": "GHB_H",
    "2015-2016": "GHB_I",
    "2017-2018": "GHB_J",
}

# ---------------------------------------------------------------
# Mortality files (one per cycle, fixed-width .dat format)
# ---------------------------------------------------------------
MORT_BASE = "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/datalinkage/linked_mortality"
MORT_FILES = {
    "1999-2000": "NHANES_1999_2000_MORT_2019_PUBLIC.dat",
    "2001-2002": "NHANES_2001_2002_MORT_2019_PUBLIC.dat",
    "2003-2004": "NHANES_2003_2004_MORT_2019_PUBLIC.dat",
    "2005-2006": "NHANES_2005_2006_MORT_2019_PUBLIC.dat",
    "2007-2008": "NHANES_2007_2008_MORT_2019_PUBLIC.dat",
    "2009-2010": "NHANES_2009_2010_MORT_2019_PUBLIC.dat",
    "2011-2012": "NHANES_2011_2012_MORT_2019_PUBLIC.dat",
    "2013-2014": "NHANES_2013_2014_MORT_2019_PUBLIC.dat",
    "2015-2016": "NHANES_2015_2016_MORT_2019_PUBLIC.dat",
    "2017-2018": "NHANES_2017_2018_MORT_2019_PUBLIC.dat",
}


def download_file(url, local_path, description=""):
    """Download a single file using curl (handles CDC redirects properly)."""

    # Skip if file already exists AND is large enough to be real data
    # Bad downloads from the old URL were ~20 KB HTML error pages
    min_size = 50 if local_path.endswith(".XPT") else 10
    if os.path.exists(local_path):
        size_kb = os.path.getsize(local_path) / 1024
        if size_kb > min_size:
            print(f"  SKIP ({size_kb:.0f} KB): {description}")
            return True
        else:
            os.remove(local_path)

    try:
        result = subprocess.run(
            [
                "curl",
                "-L",              # Follow redirects
                "-f",              # Fail on HTTP errors
                "-s",              # Silent
                "-S",              # Show errors
                "-o", local_path,
                "-m", "120",       # Max 120 seconds
                url,
            ],
            capture_output=True,
            text=True,
            timeout=130,
        )

        if result.returncode == 0 and os.path.exists(local_path):
            size_kb = os.path.getsize(local_path) / 1024
            if local_path.endswith(".XPT") and size_kb < 50:
                os.remove(local_path)
                print(f"  FAILED (too small, {size_kb:.0f} KB): {description}")
                return False
            print(f"  OK ({size_kb:.0f} KB): {description}")
            return True
        else:
            error_msg = result.stderr.strip() if result.stderr else f"exit code {result.returncode}"
            print(f"  FAILED: {description} -- {error_msg}")
            if os.path.exists(local_path):
                os.remove(local_path)
            return False

    except Exception as e:
        print(f"  FAILED: {description} -- {e}")
        if os.path.exists(local_path):
            os.remove(local_path)
        return False


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    total = 0
    success = 0
    failed = []

    print("=" * 60)
    print("NHANES Data Downloader (v3 - corrected URLs)")
    print("Cancer Survivorship & Comorbidity Mortality Project")
    print("=" * 60)
    print(f"Saving to: {DATA_DIR}\n")

    # --- Download survey components ---
    for cycle, start_year, suffix in CYCLES:
        print(f"\n--- {cycle} ---")

        # Standard components
        for comp_name, base in STANDARD_COMPONENTS.items():
            table = f"{base}{suffix}"
            url = f"{NHANES_BASE}/{start_year}/DataFiles/{table}.XPT"
            local = os.path.join(DATA_DIR, f"{cycle}_{comp_name}.XPT")
            total += 1
            if download_file(url, local, f"{comp_name} ({table}.XPT)"):
                success += 1
            else:
                failed.append(f"{cycle} {comp_name}")

        # HbA1c (special naming)
        hba1c_table = HBA1C_FILES[cycle]
        url = f"{NHANES_BASE}/{start_year}/DataFiles/{hba1c_table}.XPT"
        local = os.path.join(DATA_DIR, f"{cycle}_ghb.XPT")
        total += 1
        if download_file(url, local, f"HbA1c ({hba1c_table}.XPT)"):
            success += 1
        else:
            failed.append(f"{cycle} HbA1c")

    # --- Download mortality files ---
    print(f"\n--- Linked Mortality Files (2019 follow-up) ---")
    for cycle_label, mort_fname in MORT_FILES.items():
        url = f"{MORT_BASE}/{mort_fname}"
        local = os.path.join(DATA_DIR, f"{cycle_label}_mortality.dat")
        total += 1
        if download_file(url, local, f"{cycle_label} mortality"):
            success += 1
        else:
            failed.append(f"{cycle_label} mortality")

    # --- Summary ---
    print("\n" + "=" * 60)
    print(f"DOWNLOAD COMPLETE: {success}/{total} files succeeded")
    if failed:
        print(f"\nFailed downloads ({len(failed)}):")
        for f in failed:
            print(f"  - {f}")
        print("\nRetry by running this script again.")
    else:
        print("All files downloaded successfully!")
    print("=" * 60)

    # --- Verify ---
    xpt_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".XPT")]
    dat_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".dat")]
    print(f"\nFiles in data/: {len(xpt_files)} .XPT, {len(dat_files)} .dat mortality")

    if xpt_files:
        sizes = [os.path.getsize(os.path.join(DATA_DIR, f)) / 1024 for f in xpt_files]
        print(f"XPT sizes: min={min(sizes):.0f} KB, max={max(sizes):.0f} KB, avg={sum(sizes)/len(sizes):.0f} KB")

    return len(failed) == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
