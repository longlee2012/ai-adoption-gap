"""
Step 2a: download every Eurostat dataset the project needs, in one go.

It reuses the functions from ingest_eurostat.py, so each dataset is saved twice in
data/raw/: the untouched JSON and a tidy CSV.

Run it from the project folder:
    python src/download_all.py
"""

from ingest_eurostat import RAW_DIR, describe, fetch_dataset, save_raw, to_tidy

# dataset code -> why the project needs it
DATASETS = {
    "isoc_eb_ai": "Q1, Q3, Q4: AI use, reasons and purposes by firm size",
    "isoc_eb_ain2": "Q2: AI use by sector",
    "isoc_ske_itspe": "Why: firms employing ICT specialists, by size",
    "isoc_cicce_use": "Why: cloud computing use, by size",
    "isoc_e_dii": "Why: digital intensity, by size",
}


def main() -> None:
    for code, purpose in DATASETS.items():
        print("=" * 70)
        print(f"{code}  ({purpose})")
        try:
            data = fetch_dataset(code)
        except Exception as error:  # one failed download shouldn't stop the others
            print(f"FAILED: {error}")
            continue
        save_raw(code, data)
        describe(data)
        tidy = to_tidy(data)
        tidy.to_csv(RAW_DIR / f"{code}_tidy.csv", index=False)
        print(f"Saved {len(tidy)} rows to data/raw/{code}_tidy.csv")


if __name__ == "__main__":
    main()
