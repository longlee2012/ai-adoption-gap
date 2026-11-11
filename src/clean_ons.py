"""
Step 3b: reshape the ONS chart files into the same 8 columns as eurostat_long.csv.

ONS chart files are not tidy: a few lines of title and notes, then a header row, then the
data in WIDE format (one column per size band or per measure). This script:
  1. Finds the header row in each file and reads the table under it.
  2. Melts it to LONG format: one row per number.
  3. Maps ONS labels to Eurostat-style codes: size bands (10 - 49 -> 10-49), industries
     (Construction -> F), and its own UK_ indicator codes (never Eurostat's, because the
     survey questions differ).
  4. Saves data/clean/ons_long.csv (8 columns, same as eurostat_long.csv) and
     data/clean/ons_waves.csv (the exact survey-wave dates for the trend figures).

The UK table is kept SEPARATE from the EU table: it is a different survey, so it is shown
alongside EU figures, not merged into them.

Run it from the project folder (after ingest_ons.py):
    python src/clean_ons.py
"""

import csv
import io
import re
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
ONS_DIR = PROJECT_DIR / "data" / "raw" / "ons"
CLEAN_DIR = PROJECT_DIR / "data" / "clean"

COLUMNS = ["dataset", "geo", "time", "size_emp", "nace_r2", "indic_is", "unit", "value"]

# ONS size band -> Eurostat size code. 50-99 and 100-249 are kept separate: merging them
# into 50-249 would need a weighted average by number of firms.
SIZE_MAP = {
    "0 - 9": "0-9", "0 to 9": "0-9",
    "10 - 49": "10-49", "10 to 49": "10-49",
    "50 - 99": "50-99", "50 to 99": "50-99",
    "100 - 249": "100-249", "100 to 249": "100-249",
    "250 +": "GE250",
}

# ONS industry name -> NACE section letter (UK SIC 2007 sections use the same letters).
# P, Q and R are not in the Eurostat AI survey, so they have no EU match.
# ONS "Other service activities" is all of section S; Eurostat only covers S95.1.
NACE_MAP = {
    "Manufacturing": "C",
    "Construction": "F",
    "Wholesale and retail trade; repair of motor vehicles and motorcycles": "G",
    "Transportation and storage": "H",
    "Accommodation and food service activities": "I",
    "Information and communication": "J",
    "Real estate activities": "L",
    "Professional scientific and technical activities": "M",
    "Administrative and support service activities": "N",
    "Education": "P",
    "Human health and social work activities": "Q",
    "Arts entertainment and recreation": "R",
    "Other service activities": "S",
}

# ONS column/row label -> UK indicator code
INDICATORS = {
    # Fig 1 and Fig 2
    "Percentage of businesses reporting AI use": "UK_AI_ANY",
    "Average number of AI technologies used": "UK_AI_NTECH_AVG",
    # Fig 3: the two parts add up to UK_AI_ANY
    "Two or more use cases": "UK_AI_GE2",
    "Single use case": "UK_AI_1",
    # Fig 5: uses
    "Improve business operations": "UK_USE_OPERATIONS",
    "Provide or personalise products or services to customers": "UK_USE_CUSTOMERS",
    "Develop a new product or service": "UK_USE_NEWPRODUCT",
    "Explore a new market": "UK_USE_NEWMARKET",
    # Fig 6: how AI was obtained
    "Using free-to-use software": "UK_ADOPT_FREE",
    "Through purchase of external software or ready-to-use": "UK_ADOPT_BUY",
    "Developed in-house": "UK_ADOPT_INHOUSE",
    "Outsourced to external providers or third parties": "UK_ADOPT_OUTSOURCE",
    "Other": "UK_ADOPT_OTHER",
    # Fig 10: barriers
    "Business has not been prevented or experienced delays in the adoption of artificial "
    "intelligence technologies": "UK_BAR_NONE",
    "Level of expertise in artificial intelligence": "UK_BAR_EXPERTISE",
    "Cost": "UK_BAR_COST",
    "Difficulty identifying business use cases": "UK_BAR_USECASE",
    "Lack of trust in artificial intelligence technology product safety or transparency":
        "UK_BAR_TRUST",
    "Security concerns": "UK_BAR_SECURITY",
    "Employee concern about any potential impact of using artificial intelligence "
    "technologies": "UK_BAR_EMPLOYEES",
    "Concerns about government regulations or industry standards": "UK_BAR_REGULATION",
    "Product or service availability": "UK_BAR_AVAILABILITY",
    # Fig 12: building AI skills
    "Training or retraining existing staff": "UK_SKILL_TRAIN",
    "Automating or replacing roles with artificial intelligence technologies":
        "UK_SKILL_AUTOMATE",
    "Recruiting new staff with artificial intelligence related skills": "UK_SKILL_RECRUIT",
    "Outsourcing roles": "UK_SKILL_OUTSOURCE",
}

# One entry per figure. "rows" says what the first column holds, and the other fixed
# columns fill in what the chart doesn't vary.
#   size_emp: GE10 = firms with 10+ employees (stated in the notes);
#             TOTAL = all sizes, used where the chart doesn't state the population (check)
#   unit:     PC_ENT = % of all firms; PC_ENT_AI_TANY = % of firms using AI;
#             AVG_ENT_AI_TANY = average among AI users (not a percentage)
FIGURES = {
    "fig01_ai_use_trend.csv": dict(
        dataset="ons_bics_fig01", rows="wave", size_emp="GE10", unit="PC_ENT"),
    "fig02_ai_depth_trend.csv": dict(
        dataset="ons_bics_fig02", rows="wave", size_emp="GE10", unit="AVG_ENT_AI_TANY"),
    "fig03_ai_use_by_industry.csv": dict(
        dataset="ons_bics_fig03", rows="industry", size_emp="TOTAL", unit="PC_ENT",
        time=2026),
    "fig05_ai_uses_by_size.csv": dict(
        dataset="ons_bics_fig05", rows="indicator", unit="PC_ENT_AI_TANY", time=2026),
    "fig06_ai_adoption_method_by_industry.csv": dict(
        dataset="ons_bics_fig06", rows="industry", size_emp="TOTAL", unit="PC_ENT_AI_TANY",
        time=2026),
    "fig10_barriers_by_size.xlsx": dict(
        dataset="ons_bics_fig10", rows="size", unit="PC_ENT", time=2026, scale=100),
    "fig12_ai_skills_by_size.csv": dict(
        dataset="ons_bics_fig12", rows="indicator", unit="PC_ENT", time=2026),
}


def tidy_label(text) -> str:
    """Remove <br> tags, extra spaces and trailing spaces from an ONS label."""
    text = re.sub(r"<br>", " ", str(text), flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def read_rows(path: Path) -> list[list]:
    """Read every row of a chart file, CSV or Excel, as a list of cells."""
    if path.suffix == ".xlsx":
        sheet = pd.read_excel(path, header=None, dtype=object)
        return [[c for c in row if pd.notna(c)] for row in sheet.itertuples(index=False)]
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:  # Fig 3's notes use Windows curly quotes
        text = raw.decode("cp1252")
    return list(csv.reader(io.StringIO(text)))


def read_table(path: Path) -> pd.DataFrame:
    """Find the header row (it starts with "Date" or "Industry") and return the table."""
    rows = read_rows(path)
    for i, row in enumerate(rows):
        if row and str(row[0]).startswith(("Date", "Industry")):
            header = [tidy_label(c) for c in row]
            body = [r for r in rows[i + 1:] if r and str(r[0]).strip()]
            return pd.DataFrame([r[: len(header)] for r in body], columns=header)
    raise ValueError(f"No header row found in {path.name}")


def parse_wave(label: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """'18 September 2023 to 1 October 2023' -> (start date, end date)."""
    label = label.replace("<BR>", "").replace("<br>", " ")  # Fig 2 has "Oc<BR>tober"
    start, end = re.split(r"\s+to\s+", re.sub(r"\s+", " ", label).strip())
    return pd.to_datetime(start, format="%d %B %Y"), pd.to_datetime(end, format="%d %B %Y")


def clean_figure(file_name: str, spec: dict) -> pd.DataFrame:
    table = read_table(ONS_DIR / file_name)
    first = table.columns[0]
    long = table.melt(id_vars=first, var_name="column", value_name="value")

    rows = spec["rows"]
    if rows == "wave":  # rows are survey waves, the only column is the measure
        dates = long[first].map(parse_wave)
        long["wave_start"] = pd.to_datetime(dates.str[0])
        long["wave_end"] = pd.to_datetime(dates.str[1])
        long["time"] = long["wave_end"].dt.year  # year of the wave's END date
        long["indic_is"] = long["column"].map(INDICATORS)
        long["nace_r2"] = "ALL"
    elif rows == "industry":  # rows are industries, columns are measures
        long["nace_r2"] = long[first].map(tidy_label).map(NACE_MAP)
        long["indic_is"] = long["column"].map(INDICATORS)
    elif rows == "indicator":  # rows are measures, columns are size bands
        long["indic_is"] = long[first].map(tidy_label).map(INDICATORS)
        long["size_emp"] = long["column"].map(SIZE_MAP)
        long["nace_r2"] = "ALL"
    elif rows == "size":  # rows are size bands, columns are measures
        long["size_emp"] = long[first].map(tidy_label).map(SIZE_MAP)
        long["indic_is"] = long["column"].map(INDICATORS)
        long["nace_r2"] = "ALL"

    for column in ["size_emp", "time"]:
        if column in spec:
            long[column] = spec[column]
    long["dataset"] = spec["dataset"]
    long["geo"] = "UK"
    long["unit"] = spec["unit"]

    # Every label must have a mapping; a new or renamed ONS label stops the script here
    for column in ["indic_is", "nace_r2", "size_emp"]:
        unmapped = long.loc[long[column].isna(), [first, "column"]].drop_duplicates()
        if len(unmapped):
            raise ValueError(f"{file_name}: no {column} mapping for\n{unmapped.to_string()}")

    # "[c]" = confidential, suppressed by ONS. It becomes missing and is dropped.
    long["value"] = pd.to_numeric(long["value"], errors="coerce") * spec.get("scale", 1)
    suppressed = long["value"].isna().sum()
    if suppressed:
        print(f"  {file_name}: {suppressed} suppressed value(s) dropped")
    long = long.dropna(subset=["value"])
    long["value"] = long["value"].round(2)

    extra = ["wave_start", "wave_end"] if rows == "wave" else []
    return long[COLUMNS + extra]


def add_fig03_total(df: pd.DataFrame) -> pd.DataFrame:
    """Fig 3 splits AI users into 1 and 2+ technologies; their sum is AI use (UK_AI_ANY)."""
    parts = df[df["dataset"] == "ons_bics_fig03"]
    keys = [c for c in COLUMNS if c not in ("indic_is", "value")]
    total = parts.groupby(keys, as_index=False)["value"].sum()
    total["indic_is"] = "UK_AI_ANY"
    total["value"] = total["value"].round(2)
    return pd.concat([df, total[COLUMNS]], ignore_index=True)


def main() -> None:
    parts = []
    for file_name, spec in FIGURES.items():
        if not (ONS_DIR / file_name).exists():
            print(f"Skipping {file_name}: file not found in data/raw/ons/")
            continue
        part = clean_figure(file_name, spec)
        print(f"{spec['dataset']}: {len(part)} values")
        parts.append(part)
    combined = pd.concat(parts, ignore_index=True)

    waves = combined.dropna(subset=["wave_start"])
    waves = waves[["dataset", "indic_is", "wave_start", "wave_end", "time", "value"]]

    # The trend has several waves per year but the 8-column table has one row per year,
    # so it keeps each year's LATEST wave. Every wave stays in ons_waves.csv.
    latest = waves.groupby(["dataset", "indic_is", "time"])["wave_end"].transform("max")
    older_waves = waves.index[waves["wave_end"] != latest]
    clean = add_fig03_total(combined.drop(older_waves)[COLUMNS])

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    clean.to_csv(CLEAN_DIR / "ons_long.csv", index=False)
    waves.to_csv(CLEAN_DIR / "ons_waves.csv", index=False, date_format="%Y-%m-%d")
    print(f"\n{len(clean)} rows saved to data/clean/ons_long.csv")
    print(f"{len(waves)} trend points with exact wave dates saved to data/clean/ons_waves.csv")

    # Checks against the ONS article
    trend = waves[waves["indic_is"] == "UK_AI_ANY"].sort_values("wave_end")
    print(f"\nHeadline check, UK firms 10+ using AI: {trend['value'].iloc[0]}% "
          f"({trend['wave_end'].iloc[0]:%b %Y}) -> {trend['value'].iloc[-1]}% "
          f"({trend['wave_end'].iloc[-1]:%b %Y}); article says about 12% -> about 35%")
    duplicates = clean.duplicated(subset=[c for c in COLUMNS if c != "value"]).sum()
    print(f"Duplicate rows: {duplicates}")
    print("\nRows per dataset in ons_long.csv:")
    print(clean.groupby("dataset").size().to_string())


if __name__ == "__main__":
    main()
