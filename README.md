# Why are small businesses falling behind in AI adoption?

An end-to-end data analytics project using **Python, SQL, Excel and Power BI** to measure the AI adoption gap between small and large businesses in Europe and the UK, and to explore why it exists.

> **Status:** in progress. Steps 1 and 2 of 8 are complete: five Eurostat datasets are pulled through the API, combined into one clean table and validated.

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

## Data

| Source | What it covers | Access |
| --- | --- | --- |
| [Eurostat: Artificial intelligence by size class of enterprise](https://ec.europa.eu/eurostat/databrowser/view/isoc_eb_ai/default/table) (`isoc_eb_ai`) | AI use, purposes, reasons for non-use, by firm size; 2021, 2023-2025 | Eurostat REST API (JSON-stat), no key needed |
| [Eurostat: Artificial intelligence by NACE Rev. 2 activity](https://ec.europa.eu/eurostat/databrowser/view/isoc_eb_ain2/default/table) (`isoc_eb_ain2`) | The same indicators by sector (all firms with 10+ employees, no size split); 2021, 2023-2025 | Eurostat API |
| [Eurostat: Enterprises that employ ICT specialists](https://ec.europa.eu/eurostat/databrowser/view/isoc_ske_itspe/default/table) (`isoc_ske_itspe`) | Skills, by firm size; 2022, 2024 | Eurostat API |
| [Eurostat: Cloud computing services](https://ec.europa.eu/eurostat/databrowser/view/isoc_cicce_use/default/table) (`isoc_cicce_use`) | Cloud use, by firm size; 2021, 2023-2025 | Eurostat API |
| [Eurostat: Digital Intensity Index](https://ec.europa.eu/eurostat/databrowser/view/isoc_e_dii/default/table) (`isoc_e_dii`) | Digital intensity, by firm size; 2021-2025 | Eurostat API |
| [ONS Business Insights and Conditions Survey](https://www.ons.gov.uk/economy/economicoutputandproductivity/output/datasets/businessinsightsandimpactontheukeconomy) | UK, 2023 to 2026 | Excel downloads, planned for Step 3 |

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

All five datasets come from Eurostat's *ICT usage in enterprises* survey, so they share the same columns and size groups and can be stacked into one table. The combined table adds a `dataset` column (which file each row came from) and `nace_r2` (sector).

Every code, with its official label, is in the codebooks in `docs/` (one per dataset).

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
- The UK is not in Eurostat data after Brexit; UK figures will come from ONS and will be harmonised to Eurostat's size groups.
- Survey data shows what firms report and what goes together, not what causes the gap.

## Project structure

```
ai-adoption-gap/
  data/raw/              # data downloaded from the API, untouched (JSON + tidy CSV)
  data/clean/            # eurostat_long.csv: all datasets combined and filtered
  docs/                  # codebooks for each dataset
  src/
    ingest_eurostat.py   # downloads one Eurostat dataset and converts it to a tidy table
    download_all.py      # downloads all five datasets in one go
    combine.py           # combines them into one clean table and prints a coverage check
    make_codebook.py     # builds a codebook of every code with plain-English notes
  requirements.txt
```

## How to run

Requires Python 3.11+.

```
python -m venv .venv
.venv\Scripts\activate              # Windows (Mac: source .venv/bin/activate)
pip install -r requirements.txt

python src/download_all.py          # downloads all five datasets to data/raw/
python src/combine.py               # writes data/clean/eurostat_long.csv
python src/make_codebook.py isoc_eb_ai   # writes docs/codebook_isoc_eb_ai.csv (repeat per dataset)
```

`ingest_eurostat.py` downloads a single dataset, for example `python src/ingest_eurostat.py isoc_eb_ain2`.

**Tip:** open the CSVs in Excel through *Data > From Text/CSV* and set `size_emp` to Text, otherwise Excel turns `10-49` into a date.

## Roadmap

- [x] **Step 1:** pull data from the Eurostat API, understand the dataset, build a codebook
- [x] **Step 2:** pull sector and "digital foundations" datasets (ICT specialists, cloud, digital intensity), combine and validate
- [ ] **Step 3:** add UK data from ONS and harmonise size groups, years and sectors
- [ ] **Step 4:** SQL model with one view per question
- [ ] **Step 5:** analysis in Python (gap trend, sector gaps, drivers)
- [ ] **Step 6:** reconcile results against published figures in Excel
- [ ] **Step 7:** Power BI dashboard
- [ ] **Step 8:** final write-up and findings

## Author

**Thanh Long**, aspiring Data Analyst based in the UK. [LinkedIn](https://www.linkedin.com/) · [GitHub](https://github.com/longlee2012)
