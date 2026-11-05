"""
Step 2b: combine all the tidy Eurostat files into ONE clean table.

What it does:
  1. Reads every data/raw/*_tidy.csv file.
  2. Gives them all the same columns, filling a default where a dataset doesn't have one
     (e.g. a sector dataset has no size_emp column, so it gets "GE10" = all firms 10+).
  3. Keeps only the project scope: EU-27 countries plus the EU total, years 2021 onwards,
     and one level of sectors (NACE sections).
  4. Adds a "dataset" column so you always know where each number came from.
  5. Saves data/clean/eurostat_long.csv and prints a coverage check.

Run it from the project folder (after download_all.py):
    python src/combine.py
"""

from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
CLEAN_DIR = PROJECT_DIR / "data" / "clean"

COLUMNS = ["dataset", "geo", "time", "size_emp", "nace_r2", "indic_is", "unit", "value"]
DEFAULTS = {"size_emp": "GE10", "nace_r2": "ALL"}  # used when a dataset lacks the column

EU27 = [
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR", "HR", "HU",
    "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK",
]
SCOPE_GEO = EU27 + ["EU27_2020"]
FIRST_YEAR = 2021

# One level of sectors only (NACE sections), so no firm is counted twice. "ALL" is the
# default for datasets without sectors; C10-S951_X_K is Eurostat's all-sector total.
SECTORS = ["ALL", "C10-S951_X_K", "C", "D", "E", "F", "G", "H", "I", "J", "L", "M", "N", "S951"]


def load_one(path: Path) -> pd.DataFrame:
    code = path.name.replace("_tidy.csv", "")
    # dtype=str keeps codes like "10-49" as text; value is converted back to a number below
    df = pd.read_csv(path, dtype=str)
    df["dataset"] = code
    for column, default in DEFAULTS.items():
        if column not in df.columns:
            df[column] = default
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        print(f"Skipping {code}: no column(s) {missing}. Check it with describe().")
        return pd.DataFrame(columns=COLUMNS)
    return df[COLUMNS]


def main() -> None:
    files = sorted(RAW_DIR.glob("*_tidy.csv"))
    combined = pd.concat([load_one(f) for f in files], ignore_index=True)

    combined["time"] = pd.to_numeric(combined["time"], errors="coerce")
    combined["value"] = pd.to_numeric(combined["value"], errors="coerce")
    in_scope = (
        combined["geo"].isin(SCOPE_GEO)
        & (combined["time"] >= FIRST_YEAR)
        & combined["nace_r2"].isin(SECTORS)
    )
    clean = combined[in_scope].dropna(subset=["value"])

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CLEAN_DIR / "eurostat_long.csv"
    clean.to_csv(out_path, index=False)
    print(f"{len(combined)} rows read, {len(clean)} kept in scope, saved to {out_path}\n")

    # Coverage check: what each dataset gives you after filtering
    coverage = clean.groupby("dataset").agg(
        rows=("value", "size"),
        countries=("geo", "nunique"),
        years=("time", lambda s: ", ".join(str(int(y)) for y in sorted(s.unique()))),
        size_groups=("size_emp", lambda s: ", ".join(sorted(s.unique()))),
        sectors=("nace_r2", "nunique"),
    )
    print(coverage.to_string())


if __name__ == "__main__":
    main()
