"""
Step 1: download one Eurostat dataset through the API and look inside it.

What this script does:
  1. Calls the Eurostat API for a dataset (default: isoc_eb_ai, AI use by firm size).
  2. Saves the raw JSON response to data/raw/ so you never need to download it twice.
  3. Prints the dataset's dimensions (country, size class, indicator, year...) and their categories.
  4. Turns the JSON-stat response into a tidy table (one row per value) and saves it as CSV.

Run it from the project folder:
    python src/ingest_eurostat.py              # default dataset
    python src/ingest_eurostat.py isoc_eb_ain2 # another dataset
"""

import json
import sys
from itertools import product
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"


def fetch_dataset(code: str) -> dict:
    """Call the API and return the response as a Python dictionary."""
    params = {"format": "JSON", "lang": "EN"}
    print(f"Requesting {code} from Eurostat...")
    response = requests.get(f"{BASE_URL}/{code}", params=params, timeout=120)
    response.raise_for_status()  # stops here with an error if the server said no (e.g. 404)
    return response.json()


def save_raw(code: str, data: dict) -> Path:
    """Save the untouched response, so the raw data is always reproducible."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{code}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def describe(data: dict) -> None:
    """Print what the dataset contains: its dimensions and their categories."""
    print(f"\nDataset: {data['label']}")
    print(f"Last updated: {data.get('updated')}")
    print(f"Number of values: {len(data['value'])}\n")
    for dim_id in data["id"]:
        labels = data["dimension"][dim_id]["category"]["label"]
        print(f"- {dim_id} ({len(labels)} categories)")
        for code, label in list(labels.items())[:100]:
            print(f"    {code}: {label}")
        if len(labels) > 100:
            print(f"    ... and {len(labels) - 100} more")


def to_tidy(data: dict) -> pd.DataFrame:
    """
    Turn JSON-stat into a tidy table.

    JSON-stat stores all values in one flat list. Position 0 is the first category of
    every dimension, position 1 moves the last dimension on by one, and so on, like an
    odometer. itertools.product walks the categories in that same order, so the n-th
    combination matches flat position n.
    """
    dim_ids = data["id"]
    codes_per_dim = []
    for dim_id in dim_ids:
        index = data["dimension"][dim_id]["category"]["index"]
        codes_per_dim.append(sorted(index, key=index.get))  # categories in position order

    values = data["value"]  # a dict like {"0": 12.5, "7": 30.1}; missing keys = no data
    rows = []
    for position, combo in enumerate(product(*codes_per_dim)):
        value = values.get(str(position))
        if value is not None:
            rows.append(dict(zip(dim_ids, combo), value=value))
    return pd.DataFrame(rows)


def main() -> None:
    code = sys.argv[1] if len(sys.argv) > 1 else "isoc_eb_ai"
    data = fetch_dataset(code)
    raw_path = save_raw(code, data)
    print(f"Saved raw JSON to {raw_path}")

    describe(data)

    tidy = to_tidy(data)
    csv_path = RAW_DIR / f"{code}_tidy.csv"
    tidy.to_csv(csv_path, index=False)
    print(f"\nTidy table: {len(tidy)} rows, saved to {csv_path}")
    print(tidy.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
