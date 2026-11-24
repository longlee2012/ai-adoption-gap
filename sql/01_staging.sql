-- =====================================================================
-- 01_staging.sql
-- Load the clean CSV files into tables with the RIGHT data types.
--
-- Why: a CSV has no types. If the database guesses, "10-49" can become a
-- date and "2025" a decimal. Staging fixes the types once, so every view
-- built on top can trust them. Nothing is filtered or renamed here.
-- =====================================================================

-- Eurostat: the combined table from Step 2 (234,576 rows)
CREATE OR REPLACE TABLE stg_eurostat AS
SELECT
    dataset,
    geo,
    CAST(time AS INTEGER)  AS year,
    size_emp,
    nace_r2,
    indic_is,
    unit,
    CAST(value AS DOUBLE)  AS value
FROM read_csv(
    'data/clean/eurostat_long.csv',
    header = true,
    all_varchar = true          -- read everything as text first, then cast on purpose
);

-- Eurostat business structure: number of firms by sector and size (Q2).
-- Only the EU total was downloaded (see download_all.py). Counts, not percentages.
CREATE OR REPLACE TABLE stg_sbs AS
SELECT
    geo,
    CAST(time AS INTEGER)  AS year,
    size_emp,
    nace_r2,
    indic_sbs,
    CAST(value AS DOUBLE)  AS value
FROM read_csv(
    'data/raw/sbs_sc_ovw_tidy.csv',
    header = true,
    all_varchar = true
);

-- UK: the ONS figures cleaned in Step 3, same 8 columns as Eurostat.
-- A separate table on purpose: different survey, so never stacked with the EU rows.
CREATE OR REPLACE TABLE stg_ons AS
SELECT
    dataset,
    geo,
    CAST(time AS INTEGER)  AS year,
    size_emp,
    nace_r2,
    indic_is,
    unit,
    CAST(value AS DOUBLE)  AS value
FROM read_csv(
    'data/clean/ons_long.csv',
    header = true,
    all_varchar = true
);
