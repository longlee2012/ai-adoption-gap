# Why are small businesses falling behind in AI adoption?

An end-to-end data analytics project using **Python, SQL, Excel and Power BI** to measure the AI adoption gap between small and large businesses in Europe and the UK, and to explore why it exists.

> **Status:** in progress. Steps 1 to 4 of 8 are complete: Eurostat survey data is pulled through the API, combined and validated; UK figures from ONS are cleaned into the same format; and a SQL model answers each question with its own view, checked by automated data tests.

## The question

**Main question:** Why are small businesses falling behind large ones in AI adoption?

1. How big is the gap, and is it growing or shrinking?
2. Does the gap look the same in every sector?
3. What reasons do small businesses give for not using AI?
4. Are small and large firms using AI for different things?

**Scope:** EU countries and the UK.

## Early findings (EU, all sectors)

First look at the Eurostat data, before full analysis:

| Share of firms using at least one AI technology | 2021 | 2025 |
| --- | --- | --- |
| Small firms (10-49 employees) | 6.1% | 17.0% |
| Large firms (250+ employees) | 28.4% | 55.0% |
| **Gap (percentage points)** | 22 | **38** |
| **Large ÷ small** | 4.6× | **3.2×** |

- **The gap in percentage points is widening, but small firms are catching up in relative terms.** Which one you look at changes the story, so the project tracks both.
- **Top reason for not using AI is lack of expertise**, cited by 71% of small firms that considered AI. Small firms are also twice as likely as large ones to say AI is "not useful" for them (19% vs 10%).
- **The biggest difference in how AI is used is ICT security**: 14.5% of small AI-using firms vs 47.5% of large ones.
- **AI use varies more than fivefold by sector**: from 62.5% in information and communication to 10.8% in construction (2025, all firms with 10+ employees).

### Small firms also lag on the foundations AI needs

| EU, % of firms | Small (10-49) | Large (250+) | Year |
| --- | --- | --- | --- |
| Use at least one AI technology | 17.0% | 55.0% | 2025 |
| Employ IT specialists | 14.0% | 78.4% | 2024 |
| Buy cloud computing services | 49.3% | 84.7% | 2025 |
| Reach at least a basic level of digital intensity | 68.9% | 96.4% | 2025 |

Small firms trail on skills, cloud and digital basics as well as on AI. Whether these gaps move together across countries is tested in Step 5.

### The UK shows the same pattern

| UK, % of firms with 10+ employees using AI | 2023 | 2024 | 2025 | 2026 |
| --- | --- | --- | --- | --- |
| All sizes (ONS BICS) | 11.8% | 18.2% | 28.7% | 34.9% |

- **UK AI use roughly tripled in three years.** ONS does not split this trend by firm size, so the UK gap over time cannot be measured directly.
- **Sectors rank almost the same in the EU and the UK.** Information and communication comes first and professional and scientific second in both, and construction comes last of the sectors both sources cover (EU 2025 vs UK 2026).
- The EU and UK figures come from different surveys, so the project compares **patterns** (direction, ranking), not exact levels.

## Data

| Source | What it covers | Access |
| --- | --- | --- |
| [Eurostat: Artificial intelligence by size class of enterprise](https://ec.europa.eu/eurostat/databrowser/view/isoc_eb_ai/default/table) (`isoc_eb_ai`) | AI use, purposes, reasons for non-use, by firm size; 2021, 2023-2025 | Eurostat REST API (JSON-stat), no key needed |
| [Eurostat: Artificial intelligence by NACE Rev. 2 activity](https://ec.europa.eu/eurostat/databrowser/view/isoc_eb_ain2/default/table) (`isoc_eb_ain2`) | The same indicators by sector (all firms with 10+ employees, no size split); 2021, 2023-2025 | Eurostat API |
| [Eurostat: Enterprises that employ ICT specialists](https://ec.europa.eu/eurostat/databrowser/view/isoc_ske_itspe/default/table) (`isoc_ske_itspe`) | Skills, by firm size; 2022, 2024 | Eurostat API |
| [Eurostat: Cloud computing services](https://ec.europa.eu/eurostat/databrowser/view/isoc_cicce_use/default/table) (`isoc_cicce_use`) | Cloud use, by firm size; 2021, 2023-2025 | Eurostat API |
| [Eurostat: Digital Intensity Index](https://ec.europa.eu/eurostat/databrowser/view/isoc_e_dii/default/table) (`isoc_e_dii`) | Digital intensity, by firm size; 2021-2025 | Eurostat API |
| [Eurostat: Enterprise statistics by size class and NACE Rev. 2 activity](https://ec.europa.eu/eurostat/databrowser/view/sbs_sc_ovw/default/table) (`sbs_sc_ovw`) | Number of firms (`ENT_NR`) by sector and size class, used for Q2 (share of small firms per sector); EU total only; 2021-2024 | Eurostat API, filtered to `geo=EU27_2020` |
| [ONS: Artificial intelligence in UK businesses, 2023 to 2026](https://www.ons.gov.uk/businessindustryandtrade/business/businessservices/articles/artificialintelligenceinukbusinesses/2023to2026) (Business Insights and Conditions Survey, BICS) | UK AI use over time, by industry, uses, barriers and skills by size band; 2023-2026 | CSV download for each chart (ONS has no API for BICS); the barriers chart is an Excel file |

### About the data

Each row is **one percentage** describing a group of firms. You only know what it means by reading it with the other columns:

| Column | Meaning | Example |
| --- | --- | --- |
| `size_emp` | Firm size by number of employees | `10-49` small, `50-249` medium, `GE250` large |
| `indic_is` | The survey question | `E_AI_TANY` = uses at least one AI technology |
| `unit` | **What the percentage is out of** | `PC_ENT` all firms · `PC_ENT_AI_TANY` AI users · `PC_ENT_AI_EC` firms that considered AI |
| `geo` | Country or region | `DE`, `FR`, `EU27_2020` (EU total) |
| `time` | Survey year | 2021, 2023, 2024, 2025 (AI was not surveyed in 2022) |
| `value` | The percentage | `17.00` |

Example: `10-49 | E_AI_TANY | PC_ENT | EU27_2020 | 2025 | 17.00` means *"in 2025, 17% of all EU firms with 10-49 employees used at least one AI technology."*

The five `isoc_` datasets come from Eurostat's *ICT usage in enterprises* survey, so they share the same columns and size groups and can be stacked into one table. The combined table adds a `dataset` column (which file each row came from) and `nace_r2` (sector).

`sbs_sc_ovw` is different: it holds **counts of firms**, not percentages, from Eurostat's structural business statistics. It is kept in `data/raw/` as its own table and is not stacked into `eurostat_long.csv` (`combine.py` skips it).

Every code, with its official label, is in one codebook, `docs/codebook.csv` (one row per code per dataset).

### UK data (Step 3)

ONS chart files are in wide format with title and note lines above the table. `clean_ons.py` reshapes them into the **same 8 columns** as the Eurostat table and saves `data/clean/ons_long.csv` (166 rows). It also saves `data/clean/ons_waves.csv` with the exact survey dates.

- **Size bands** are mapped to Eurostat codes (`10 - 49` becomes `10-49`, `250 +` becomes `GE250`). ONS `50-99` and `100-249` are kept separate, because merging them into `50-249` would need a weighted average by number of firms.
- **Industries** are mapped to NACE section letters (UK SIC 2007 uses the same letters).
- **Indicators** get their own `UK_` codes, never Eurostat's, because the survey questions are worded differently.
- **Themes:** `docs/theme_map.csv` links EU and UK questions through a shared theme (for example "skills", "cost", "no clear use"), so reasons and uses can be compared even though the wording differs.

The UK table is kept **separate** from the EU table. It is shown alongside the EU figures, never stacked with them.

### SQL model (Step 4)

`build_db.py` builds a DuckDB database, `data/ai_gap.duckdb`, from the SQL files in `sql/`, which run in order:

| File | What it does |
| --- | --- |
| `01_staging.sql` | Loads the clean CSVs into tables with fixed data types (`stg_eurostat`, `stg_sbs`, `stg_ons`), so `10-49` never becomes a date |
| `02_dimensions.sql` | Lookup tables that turn codes into readable labels: sizes (with sort order), sectors, codes, themes |
| `03_views.sql` | One view per question (listed below) |
| `04_tests.sql` | Data tests. Each returns the problem rows, so a pass returns 0 rows. The build stops if any test fails. |

| View | Question |
| --- | --- |
| `v_q1_gap_trend` | Q1: small vs large AI use by country and year, the gap in points, the ratio and the change since the last survey |
| `v_q1_uk_trend` | Q1: UK AI use over time |
| `v_q2_sector_ai` | Q2: AI use by sector, with each sector's rank per year |
| `v_q2_sector_structure` | Q2: share of firms in each sector that are small (EU) |
| `v_q2_sector_scatter` | Q2: one row per sector, AI use against share of small firms |
| `v_q2_sector_eu_uk` | Q2: EU and UK sector rankings side by side |
| `v_q3_reasons` | Q3: reasons for not using AI, by size |
| `v_q4_purposes` | Q4: what AI is used for, by size |
| `v_themes_eu_uk` | Q3 and Q4: EU and UK reasons and uses grouped by shared theme |
| `v_why_foundations` | Why: AI, IT specialists, cloud and digital intensity by country and size |

The 14 tests check row counts, missing values, that percentages are between 0 and 100, that joins have not doubled rows, that every code has a label, and that the EU 2025 figures match Eurostat's published 17.00% and 55.03%.

Every view is exported to `data/marts/<view>.csv`, so Python (Step 5), Excel (Step 6) and Power BI (Step 7) all use the same numbers.

### Cleaning and validation

The combined table `data/clean/eurostat_long.csv` keeps:

- the 27 EU countries plus the EU total (non-EU countries and the euro area total are dropped)
- years 2021 onwards, when AI was first surveyed
- one level of sectors only (NACE sections C to N and S95.1, plus the all-sector total), so no firm is counted twice

Result: **234,576 rows, no missing values, no duplicate rows.** Key figures match Eurostat's published numbers (for example 17.00% of small and 55.03% of large EU firms used AI in 2025).

### Caveats

- Eurostat excludes firms with fewer than 10 employees in most countries, and excludes agriculture, mining and finance.
- Reasons for not using AI are asked only of firms that **considered** AI, so those percentages are not shares of all firms.
- AI by sector is not split by firm size, so the sector question is answered by comparing sector AI use with how many small firms each sector has.
- Datasets cover different years (for example IT specialists only in even years), so comparisons pair the closest years.
- The Digital Intensity Index likely counts AI as one of its 12 technologies, so its link with AI use is partly built in.
- The UK is not in Eurostat data after Brexit, so UK figures come from ONS. It is a different survey with different questions, so EU and UK levels are not directly comparable.
- The ONS trend has no size split, and ONS charts by industry may cover all firm sizes rather than 10+ only.
- ONS publishes 50-99 and 100-249 separately, so the UK has no single "medium" group to match Eurostat's 50-249.
- Survey data shows what firms report and what goes together, not what causes the gap.

## Project structure

```
ai-adoption-gap/
  data/raw/              # data downloaded untouched (Eurostat JSON + tidy CSV; ONS files in raw/ons/)
  data/clean/            # eurostat_long.csv, ons_long.csv, ons_waves.csv
  data/marts/            # one CSV per SQL view, for Python, Excel and Power BI
  data/ai_gap.duckdb     # the database built by build_db.py (not in git)
  docs/
    codebook.csv         # every code with its official label and plain-English notes
    theme_map.csv        # links EU and UK questions through shared themes
  sql/
    01_staging.sql       # load clean CSVs with fixed data types
    02_dimensions.sql    # lookup tables for labels
    03_views.sql         # one view per question
    04_tests.sql         # data tests (each must return 0 rows)
  src/
    ingest_eurostat.py   # downloads one Eurostat dataset and converts it to a tidy table
    download_all.py      # downloads all six Eurostat datasets in one go
    combine.py           # combines them into one clean table and prints a coverage check
    make_codebook.py     # builds docs/codebook.csv
    ingest_ons.py        # downloads the ONS chart CSVs
    clean_ons.py         # reshapes ONS figures into the Eurostat format
    build_db.py          # builds the database, runs the tests, exports the views
    query.py             # runs any SQL against the database (read-only)
    load_sqlserver.py    # optional: loads the CSVs into a local SQL Server
  requirements.txt
```

## How to run

Requires Python 3.11+.

```
python -m venv .venv
.venv\Scripts\activate              # Windows (Mac: source .venv/bin/activate)
pip install -r requirements.txt

# Step 1-2: Eurostat
python src/download_all.py          # downloads all six datasets to data/raw/
python src/combine.py               # writes data/clean/eurostat_long.csv
python src/make_codebook.py         # writes docs/codebook.csv

# Step 3: UK
python src/ingest_ons.py            # downloads the ONS chart CSVs to data/raw/ons/
python src/clean_ons.py             # writes data/clean/ons_long.csv and ons_waves.csv

# Step 4: SQL model
python src/build_db.py              # builds data/ai_gap.duckdb, runs the tests, writes data/marts/
```

`ingest_eurostat.py` downloads a single dataset, for example `python src/ingest_eurostat.py isoc_eb_ain2`.

`ingest_ons.py` does not download the barriers chart (`fig10_barriers_by_size.xlsx`). Save it from the ONS article into `data/raw/ons/` before running `clean_ons.py`.

**Explore the database** with `query.py`:

```
python src/query.py "SELECT * FROM v_q1_gap_trend WHERE geo = 'EU27_2020'"
python src/query.py path/to/my_query.sql
```

**Optional, SQL Server:** `python src/load_sqlserver.py` copies the clean, mart and docs CSVs into a database called `AIGap` on `localhost\SQLEXPRESS` (schemas `clean`, `marts`, `ref`). It needs SQL Server Express and ODBC Driver 17, and signs in with your Windows login.

**Tip:** open the CSVs in Excel through *Data > From Text/CSV* and set `size_emp` to Text, otherwise Excel turns `10-49` into a date.

## Roadmap

- [x] **Step 1:** pull data from the Eurostat API, understand the dataset, build a codebook
- [x] **Step 2:** pull sector and "digital foundations" datasets (ICT specialists, cloud, digital intensity), combine and validate
- [x] **Step 3:** add UK data from ONS and harmonise size groups, years and sectors
- [x] **Step 4:** SQL model with one view per question, data tests, and mart exports
- [ ] **Step 5:** analysis in Python (gap trend, sector gaps, drivers)
- [ ] **Step 6:** reconcile results against published figures in Excel
- [ ] **Step 7:** Power BI dashboard
- [ ] **Step 8:** final write-up and findings

## Author

**Thanh Long**, aspiring Data Analyst based in the UK. [LinkedIn](https://www.linkedin.com/) · [GitHub](https://github.com/longlee2012)
