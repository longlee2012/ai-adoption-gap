# Why are small businesses falling behind in AI adoption?

An end-to-end data analytics project using **Python, SQL, Excel and Power BI** to measure the AI adoption gap between small and large businesses in Europe and the UK, and to explore why it exists.

> **Status:** in progress. Step 1 of 8 (data ingestion and data understanding) is complete.

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

## Data

| Source | What it covers | Access |
| --- | --- | --- |
| [Eurostat: Artificial intelligence by size class of enterprise](https://ec.europa.eu/eurostat/databrowser/view/isoc_eb_ai/default/table) (`isoc_eb_ai`) | EU countries, 2021, 2023, 2024, 2025 | Eurostat REST API (JSON-stat), no key needed |
| Eurostat: AI by sector (`isoc_eb_ain2`) | As above, split by industry | Planned for Step 2 |
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

The full list of 63 indicators and all other codes is in the codebook: `docs/codebook_isoc_eb_ai.csv`.

### Caveats

- Eurostat excludes firms with fewer than 10 employees in most countries, and excludes agriculture, mining and finance.
- Reasons for not using AI are asked only of firms that **considered** AI, so those percentages are not shares of all firms.
- The UK is not in Eurostat data after Brexit; UK figures will come from ONS and will be harmonised to Eurostat's size groups.
- Survey data shows what firms report and what goes together, not what causes the gap.

## Project structure

```
ai-adoption-gap/
  data/raw/              # data downloaded from the API, untouched
  docs/                  # codebooks for each dataset
  src/
    ingest_eurostat.py   # downloads a Eurostat dataset and converts it to a tidy table
    make_codebook.py     # builds a codebook of every code with plain-English notes
  requirements.txt
```

## How to run

Requires Python 3.11+.

```
python -m venv .venv
.venv\Scripts\activate              # Windows (Mac: source .venv/bin/activate)
pip install -r requirements.txt

python src/ingest_eurostat.py       # downloads isoc_eb_ai to data/raw/
python src/make_codebook.py         # writes docs/codebook_isoc_eb_ai.csv
```

Pass another dataset code to either script, for example `python src/ingest_eurostat.py isoc_eb_ain2`.

**Tip:** open the CSVs in Excel through *Data > From Text/CSV* and set `size_emp` to Text, otherwise Excel turns `10-49` into a date.

## Roadmap

- [x] **Step 1:** pull data from the Eurostat API, understand the dataset, build a codebook
- [ ] **Step 2:** pull sector and "digital foundations" datasets (ICT specialists, cloud, data analytics)
- [ ] **Step 3:** add UK data from ONS and harmonise size groups, years and sectors
- [ ] **Step 4:** SQL model with one view per question
- [ ] **Step 5:** analysis in Python (gap trend, sector gaps, drivers)
- [ ] **Step 6:** reconcile results against published figures in Excel
- [ ] **Step 7:** Power BI dashboard
- [ ] **Step 8:** final write-up and findings

## Author

**Thanh Long**, aspiring Data Analyst based in the UK. [LinkedIn](https://www.linkedin.com/) · [GitHub](https://github.com/longlee2012)
