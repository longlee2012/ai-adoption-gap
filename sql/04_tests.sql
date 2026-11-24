-- =====================================================================
-- 04_tests.sql
-- Data tests. Each test is a query that returns the PROBLEM rows,
-- so a passing test returns 0 rows. build_db.py runs every query that
-- starts with a "-- test:" line and stops if any fails.
--
-- Why: views can be wrong without any error message. A typo in a filter
-- silently returns nothing, a bad join silently doubles rows. Tests catch
-- that before a wrong number reaches a chart.
-- =====================================================================

-- test: staging has the expected row count from Step 2
SELECT COUNT(*) AS rows_found FROM stg_eurostat HAVING COUNT(*) <> 234576;

-- test: no missing values in staging
SELECT * FROM stg_eurostat WHERE value IS NULL OR year IS NULL;

-- test: every percentage is between 0 and 100
SELECT * FROM stg_eurostat WHERE value < 0 OR value > 100;

-- test: Q1 has one row per country and year (no doubled rows from a join)
SELECT geo, year, COUNT(*) AS n FROM v_q1_gap_trend GROUP BY geo, year HAVING COUNT(*) > 1;

-- test: Q1 matches Eurostat's published EU 2025 figures (17.00 small, 55.03 large)
SELECT * FROM v_q1_gap_trend
WHERE geo = 'EU27_2020' AND year = 2025
  AND (ABS(small_pct - 17.00) > 0.01 OR ABS(large_pct - 55.03) > 0.01);

-- test: Q1 EU 2025 row exists (the check above passes silently if the row is missing)
SELECT 'missing EU 2025 row' AS problem
WHERE NOT EXISTS (SELECT 1 FROM v_q1_gap_trend WHERE geo = 'EU27_2020' AND year = 2025);

-- test: every sector in the AI data got a label
SELECT DISTINCT nace_r2 FROM stg_eurostat
WHERE dataset = 'isoc_eb_ain2'
  AND nace_r2 NOT IN (SELECT nace_r2 FROM dim_sector);

-- test: every sector in the scatter found its business-structure share
SELECT nace_r2, sector_label FROM v_q2_sector_scatter WHERE small_share_pct IS NULL;

-- test: small firms are a share, so between 0 and 100
SELECT * FROM v_q2_sector_structure WHERE small_share_pct < 0 OR small_share_pct > 100;

-- test: Q3 has reasons for small and large firms in the latest year
SELECT size_emp FROM (VALUES ('10-49'), ('GE250')) AS t(size_emp)
WHERE size_emp NOT IN (
    SELECT size_emp FROM v_q3_reasons
    WHERE geo = 'EU27_2020' AND year = (SELECT MAX(year) FROM v_q3_reasons)
);

-- test: Q4 has one row per country, year and purpose
SELECT geo, year, purpose_code, COUNT(*) FROM v_q4_purposes
GROUP BY geo, year, purpose_code HAVING COUNT(*) > 1;

-- test: foundations view has all four measures for the EU
SELECT * FROM v_why_foundations
WHERE geo = 'EU27_2020'
  AND (ai_use_pct IS NULL OR it_specialists_pct IS NULL
       OR cloud_pct IS NULL OR digital_basic_pct IS NULL);

-- test: UK trend has one row per year
SELECT year, COUNT(*) FROM v_q1_uk_trend GROUP BY year HAVING COUNT(*) > 1;

-- test: every EU and UK theme code is found in the data (a code typo would silently drop it)
SELECT t.source, t.code FROM dim_theme AS t
WHERE (t.source = 'eurostat' AND t.code NOT IN (SELECT indic_is FROM stg_eurostat))
   OR (t.source = 'ons'      AND t.code NOT IN (SELECT indic_is FROM stg_ons));
