"""
Medicare Claims Data Downloader
================================
Downloads CMS Medicare Inpatient and Physician PUF datasets.

Usage:
    python download_data.py

Data lands in: ./data/raw/

CMS Data Sources:
- Medicare Inpatient Hospitals by Provider and Service
  https://data.cms.gov/provider-summary-by-type-of-service/medicare-inpatient-hospitals
- Medicare Physician and Other Practitioners by Provider and Service
  https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners
"""

import os
import requests
import zipfile
from pathlib import Path

# ── Output paths ──────────────────────────────────────────────────────────────
RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# ── CMS Dataset URLs (most recent available year) ─────────────────────────────
# These are the CMS open data API endpoints.
# If a URL returns 404, go to data.cms.gov, find the dataset,
# click "Export" → "CSV", copy the direct download link and update here.

DATASETS = [
    {
        "name": "Medicare Inpatient Hospital PUF 2022",
        "filename": "inpatient_hospital_2022.csv",
        "url": (
            "https://data.cms.gov/sites/default/files/2024-05/"
            "7d1f4bcd-7dd9-4fd1-aa7f-91cd69e452d3/"
            "MUP_INP_RY24_P03_V10_DY22_PrvSvc.CSV"
        ),
    },
    {
        "name": "Medicare Physician & Other Practitioners PUF 2022",
        "filename": "physician_practitioners_2022.csv",
        "url": (
            "https://data.cms.gov/sites/default/files/2025-11/"
            "53fb2bae-4913-48dc-a6d4-d8c025906567/"
            "MUP_PHY_R25_P05_V20_D22_Prov_Svc.csv"
        ),
    },
]

# ── Fallback: CMS API endpoints (if direct file links break) ─────────────────
# Use these if the URLs above return errors.
# Replace {DATASET_ID} with the actual ID from data.cms.gov.
CMS_API_BASE = "https://data.cms.gov/data-api/v1/dataset"
FALLBACK_INSTRUCTIONS = """
If download fails, get the file manually:
1. Go to https://data.cms.gov
2. Search "Medicare Inpatient Hospitals" or "Medicare Physician Practitioners"
3. Click the dataset → Export → CSV
4. Save to ./data/raw/ with the filename shown above
"""


def download_file(name: str, url: str, dest: Path) -> bool:
    """Download a file with progress reporting."""
    if dest.exists():
        print(f"  [SKIP] {dest.name} already exists")
        return True

    print(f"  Downloading {name}...")
    print(f"  URL: {url}")

    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()

        total = int(response.headers.get("content-length", 0))
        downloaded = 0
        chunk_size = 1024 * 1024  # 1MB chunks

        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        print(f"  Progress: {pct:.0f}% ({downloaded/1e6:.1f} MB)", end="\r")

        print(f"\n  Done: {dest} ({dest.stat().st_size / 1e6:.1f} MB)")
        return True

    except requests.exceptions.HTTPError as e:
        print(f"\n  [ERROR] HTTP {e.response.status_code} — URL may have changed.")
        print(FALLBACK_INSTRUCTIONS)
        return False

    except requests.exceptions.ConnectionError:
        print("\n  [ERROR] Connection failed. Check internet and try again.")
        return False

    except Exception as e:
        print(f"\n  [ERROR] {e}")
        return False


def validate_csv(path: Path) -> None:
    """Quick sanity check: print shape and first few column names."""
    try:
        import pandas as pd
        df = pd.read_csv(path, nrows=5)
        # Get full column count without reading whole file
        with open(path) as f:
            col_count = len(f.readline().split(","))
        print(f"  Columns ({col_count}): {list(df.columns[:6])} ...")
        print(f"  Preview rows loaded: {len(df)}")
    except Exception as e:
        print(f"  [WARN] Could not validate: {e}")


def main():
    print("=" * 60)
    print("CMS Medicare Data Downloader")
    print("=" * 60)

    results = []
    for dataset in DATASETS:
        dest = RAW_DIR / dataset["filename"]
        print(f"\n[{dataset['name']}]")
        success = download_file(dataset["name"], dataset["url"], dest)
        if success and dest.exists():
            validate_csv(dest)
        results.append((dataset["name"], success))

    print("\n" + "=" * 60)
    print("Summary:")
    for name, success in results:
        status = "OK" if success else "FAILED"
        print(f"  [{status}] {name}")

    print("\nNext step: open notebooks/01_data_prep.ipynb")
    print("=" * 60)


if __name__ == "__main__":
    main()
