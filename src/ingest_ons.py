"""
Step 3a: download the UK AI figures from ONS.

ONS doesn't offer an API for its business survey (BICS), but every chart in its article
"Artificial intelligence in UK businesses: 2023 to 2026" (20 July 2026) has a CSV download.
This script fetches those CSVs, saves them untouched to data/raw/ons/, and prints the top
of each file so you can see how it's laid out before cleaning it.

Source article:
https://www.ons.gov.uk/businessindustryandtrade/business/businessservices/articles/artificialintelligenceinukbusinesses/2023to2026

Run it from the project folder:
    python src/ingest_ons.py
"""

import time
from pathlib import Path

import requests

PROJECT_DIR = Path(__file__).resolve().parent.parent
ONS_DIR = PROJECT_DIR / "data" / "raw" / "ons"

ARTICLE = "/businessindustryandtrade/business/businessservices/articles/artificialintelligenceinukbusinesses/2023to2026"
GENERATOR = "https://www.ons.gov.uk/generator"

# chart id -> (file name, what it shows, which question it helps answer)
FIGURES = {
    "808491a0": ("fig01_ai_use_trend", "AI use over time, firms with 10+ employees", "Q1"),
    "7296b513": ("fig02_ai_depth_trend", "Average number of AI technologies over time", "Q1"),
    "5376501d": ("fig03_ai_use_by_industry", "AI use by industry, June 2026", "Q2"),
    "069669a5": ("fig05_ai_uses_by_size", "What AI is used for, by size band, June 2026", "Q4"),
    "1783dc4d": ("fig06_ai_adoption_method_by_industry", "How AI was obtained, by industry", "Q4"),
    "3ca5c8d8": ("fig12_ai_skills_by_size", "How firms build AI skills, by size band", "Why"),
}


def download_figure(chart_id: str, name: str) -> Path:
    params = {"uri": f"{ARTICLE}/{chart_id}", "format": "csv"}
    headers = {"User-Agent": "ai-adoption-gap portfolio project"}
    response = requests.get(GENERATOR, params=params, headers=headers, timeout=60)
    response.raise_for_status()
    path = ONS_DIR / f"{name}.csv"
    path.write_bytes(response.content)  # bytes, untouched, exactly as ONS sent them
    return path


def main() -> None:
    ONS_DIR.mkdir(parents=True, exist_ok=True)
    for i, (chart_id, (name, what, question)) in enumerate(FIGURES.items()):
        if i:
            time.sleep(5)  # pause between requests: ONS answers 429 "Too Many Requests" otherwise
        print("=" * 70)
        print(f"{name}  ({question}: {what})")
        try:
            path = download_figure(chart_id, name)
        except Exception as error:  # one failed chart shouldn't stop the others
            print(f"FAILED: {error}")
            continue
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        print(f"Saved {len(lines)} lines to data/raw/ons/{path.name}. First 12 lines:")
        for line in lines[:12]:
            print("   ", line)


if __name__ == "__main__":
    main()
