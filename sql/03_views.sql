-- =====================================================================
-- 03_views.sql
-- One view per project question. Python (Step 5), Excel (Step 6) and
-- Power BI (Step 7) all read these views, so every tool shows the same
-- numbers.
--
-- Golden rule for this data: ALWAYS filter indic_is AND unit AND size.
-- The same indicator exists with several units (% of all firms, % of AI
-- users...). Forget the unit and you mix different percentages.
-- =====================================================================


-- ---------------------------------------------------------------------
-- Q1. How big is the gap, and is it growing or shrinking?
-- One row per country and year: small vs large AI use, the gap in
-- percentage points, the ratio, and the change since the previous survey.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_q1_gap_trend AS
WITH ai_use AS (                         -- step 1: only the rows we need
    SELECT geo, year, size_emp, value
    FROM stg_eurostat
    WHERE dataset  = 'isoc_eb_ai'
      AND indic_is = 'E_AI_TANY'         -- uses at least one AI technology
      AND unit     = 'PC_ENT'            -- % of ALL firms in the size group
      AND nace_r2 IN ('ALL', 'C10-S951_X_K')
      AND size_emp IN ('10-49', 'GE250')
),
wide AS (                                -- step 2: small and large side by side
    SELECT
        geo,
        year,
        MAX(CASE WHEN size_emp = '10-49' THEN value END) AS small_pct,
        MAX(CASE WHEN size_emp = 'GE250' THEN value END) AS large_pct
    FROM ai_use
    GROUP BY geo, year
)
SELECT
    geo,
    year,
    small_pct,
    large_pct,
    ROUND(large_pct - small_pct, 2)                       AS gap_pp,
    ROUND(large_pct / NULLIF(small_pct, 0), 2)            AS large_to_small_ratio,
    ROUND((large_pct - small_pct)
        - LAG(large_pct - small_pct) OVER (PARTITION BY geo ORDER BY year), 2)
                                                          AS gap_change_pp
FROM wide;


-- ---------------------------------------------------------------------
-- Q2a. Does the gap look the same in every sector?
-- AI use by sector (all firms 10+; Eurostat has no size split by sector),
-- with each sector's rank in its year.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_q2_sector_ai AS
SELECT
    e.geo,
    e.year,
    e.nace_r2,
    s.sector_label,
    e.value AS ai_use_pct,
    RANK() OVER (PARTITION BY e.geo, e.year ORDER BY e.value DESC) AS rank_in_year
FROM stg_eurostat AS e
JOIN dim_sector  AS s USING (nace_r2)
WHERE e.dataset  = 'isoc_eb_ain2'
  AND e.indic_is = 'E_AI_TANY'
  AND e.unit     = 'PC_ENT'
  AND e.nace_r2 <> 'C10-S951_X_K';       -- sectors only, not the total


-- ---------------------------------------------------------------------
-- Q2b. Share of firms (10+) in each sector that are small, EU total.
-- Only 10+ employees (0-9 dropped), so it describes the same firms as the AI survey.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_q2_sector_structure AS
WITH firms AS (
    SELECT
        nace_r2,
        year,
        SUM(CASE WHEN size_emp IN ('10-19', '20-49')                  THEN value END) AS small_firms,
        SUM(CASE WHEN size_emp IN ('10-19', '20-49', '50-249', 'GE250') THEN value END) AS firms_10_plus
    FROM stg_sbs
    WHERE geo = 'EU27_2020'
      AND indic_sbs = 'ENT_NR'           -- number of enterprises
      AND nace_r2 IN (SELECT nace_r2 FROM dim_sector)   -- same sections as the AI data
    GROUP BY nace_r2, year
)
SELECT
    nace_r2,
    year,
    small_firms,
    firms_10_plus,
    ROUND(100.0 * small_firms / NULLIF(firms_10_plus, 0), 2) AS small_share_pct
FROM firms;


-- ---------------------------------------------------------------------
-- Q2 joined: one dot per sector for the scatter chart.
-- Business structure changes slowly, so the latest SBS year is paired
-- with the latest AI year.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_q2_sector_scatter AS
WITH latest_ai AS (
    SELECT * FROM v_q2_sector_ai
    WHERE geo = 'EU27_2020'
      AND year = (SELECT MAX(year) FROM v_q2_sector_ai)
),
latest_sbs AS (
    SELECT * FROM v_q2_sector_structure
    WHERE year = (SELECT MAX(year) FROM v_q2_sector_structure)
)
SELECT
    a.nace_r2,
    a.sector_label,
    a.year       AS ai_year,
    a.ai_use_pct,
    b.year       AS sbs_year,
    b.small_share_pct
FROM latest_ai  AS a
LEFT JOIN latest_sbs AS b USING (nace_r2);   -- LEFT JOIN: keep a sector even if SBS has no match


-- ---------------------------------------------------------------------
-- Q3. What reasons do firms give for not using AI?
-- Base = firms that do NOT use AI but CONSIDERED it (unit PC_ENT_AI_EC),
-- so these are NOT shares of all firms.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_q3_reasons AS
SELECT
    e.geo,
    e.year,
    e.size_emp,
    d.size_label,
    e.indic_is                         AS reason_code,
    COALESCE(c.plain_english, c.official_label, e.indic_is) AS reason,
    e.value                            AS pct_of_firms_that_considered_ai,
    RANK() OVER (PARTITION BY e.geo, e.year, e.size_emp ORDER BY e.value DESC) AS rank_in_group
FROM stg_eurostat AS e
JOIN dim_size     AS d USING (size_emp)
LEFT JOIN dim_code AS c ON c.dimension = 'indic_is' AND c.code = e.indic_is
WHERE e.dataset  = 'isoc_eb_ai'
  AND e.indic_is LIKE 'E\_AI\_B%' ESCAPE '\'   -- reason codes start with E_AI_B
  AND e.indic_is NOT LIKE 'E\_AI\_BIAS%' ESCAPE '\'  -- ...but bias measures are not reasons
  AND e.unit     = 'PC_ENT_AI_EC'
  AND e.nace_r2 IN ('ALL', 'C10-S951_X_K')
  AND d.is_main_group;


-- ---------------------------------------------------------------------
-- Q4. Are small and large firms using AI for different things?
-- Base = firms that USE AI (unit PC_ENT_AI_TANY).
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_q4_purposes AS
WITH purposes AS (
    SELECT geo, year, indic_is, size_emp, value
    FROM stg_eurostat
    WHERE dataset  = 'isoc_eb_ai'
      AND indic_is IN ('E_AI_PMS', 'E_AI_PPP', 'E_AI_PBAM', 'E_AI_PLOG',
                       'E_AI_PITS', 'E_AI_PHR', 'E_AI_PFIN', 'E_AI_PRDI')
      AND unit     = 'PC_ENT_AI_TANY'
      AND nace_r2 IN ('ALL', 'C10-S951_X_K')
      AND size_emp IN ('10-49', 'GE250')
)
SELECT
    p.geo,
    p.year,
    p.indic_is                                        AS purpose_code,
    COALESCE(c.plain_english, c.official_label, p.indic_is) AS purpose,
    MAX(CASE WHEN size_emp = '10-49' THEN value END)  AS small_pct,
    MAX(CASE WHEN size_emp = 'GE250' THEN value END)  AS large_pct,
    ROUND(MAX(CASE WHEN size_emp = 'GE250' THEN value END)
        - MAX(CASE WHEN size_emp = '10-49' THEN value END), 2) AS gap_pp
FROM purposes AS p
LEFT JOIN dim_code AS c ON c.dimension = 'indic_is' AND c.code = p.indic_is
GROUP BY p.geo, p.year, p.indic_is, purpose;


-- ---------------------------------------------------------------------
-- Why. Do small firms also lag on the foundations AI needs?
-- One row per country and size group, latest year of each indicator.
-- IT specialists are only surveyed in even years, so its year is shown.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_why_foundations AS
WITH picked AS (
    SELECT
        geo, size_emp, year, value,
        CASE
            WHEN dataset = 'isoc_eb_ai'     AND indic_is = 'E_AI_TANY'  THEN 'ai_use'
            WHEN dataset = 'isoc_ske_itspe' AND indic_is = 'E_ITSP2'    THEN 'it_specialists'
            WHEN dataset = 'isoc_cicce_use' AND indic_is = 'E_CC'       THEN 'cloud'
            WHEN dataset = 'isoc_e_dii'     AND indic_is = 'E_DI3_GELO' THEN 'digital_basic'
        END AS measure
    FROM stg_eurostat
    WHERE unit = 'PC_ENT'
      AND nace_r2 IN ('ALL', 'C10-S951_X_K')
      AND size_emp IN ('10-49', '50-249', 'GE250')
),
latest AS (                              -- keep each measure's most recent year
    SELECT *
    FROM picked
    WHERE measure IS NOT NULL
    QUALIFY year = MAX(year) OVER (PARTITION BY geo, size_emp, measure)
)
SELECT
    l.geo,
    l.size_emp,
    d.size_label,
    MAX(CASE WHEN measure = 'ai_use'         THEN value END) AS ai_use_pct,
    MAX(CASE WHEN measure = 'ai_use'         THEN year  END) AS ai_year,
    MAX(CASE WHEN measure = 'it_specialists' THEN value END) AS it_specialists_pct,
    MAX(CASE WHEN measure = 'it_specialists' THEN year  END) AS it_year,
    MAX(CASE WHEN measure = 'cloud'          THEN value END) AS cloud_pct,
    MAX(CASE WHEN measure = 'digital_basic'  THEN value END) AS digital_basic_pct
FROM latest AS l
JOIN dim_size AS d USING (size_emp)
GROUP BY l.geo, l.size_emp, d.size_label;


-- =====================================================================
-- EU and UK side by side.
-- Different surveys, so compare PATTERNS (direction, ranking), never the
-- exact levels. Every view keeps a "source" column to make that visible.
-- =====================================================================

-- Q1 UK: overall AI use over time (ONS has no size split for the trend)
CREATE OR REPLACE VIEW v_q1_uk_trend AS
SELECT year, value AS ai_use_pct
FROM stg_ons
WHERE indic_is = 'UK_AI_ANY'
  AND unit     = 'PC_ENT'
  AND size_emp = 'GE10'
  AND nace_r2  = 'ALL';


-- Q2: sector ranking, EU (latest Eurostat year) next to UK (latest ONS year)
CREATE OR REPLACE VIEW v_q2_sector_eu_uk AS
WITH eu AS (
    SELECT nace_r2, year, ai_use_pct, rank_in_year
    FROM v_q2_sector_ai
    WHERE geo = 'EU27_2020'
      AND year = (SELECT MAX(year) FROM v_q2_sector_ai)
),
uk AS (
    SELECT
        nace_r2,
        year,
        value AS ai_use_pct,
        RANK() OVER (ORDER BY value DESC) AS rank_in_year
    FROM stg_ons
    WHERE dataset  = 'ons_bics_fig03'
      AND indic_is = 'UK_AI_ANY'
      AND unit     = 'PC_ENT'
      AND nace_r2 IN (SELECT nace_r2 FROM eu)   -- only sectors both surveys cover.
                                                -- UK "S" (all other services) is NOT matched to
                                                -- EU "S951" (computer repair): same letter, different scope.
)
SELECT
    s.nace_r2,
    s.sector_label,
    eu.year         AS eu_year,
    eu.ai_use_pct   AS eu_ai_use_pct,
    eu.rank_in_year AS eu_rank,
    uk.year         AS uk_year,
    uk.ai_use_pct   AS uk_ai_use_pct,
    uk.rank_in_year AS uk_rank
FROM eu
JOIN dim_sector AS s USING (nace_r2)
LEFT JOIN uk USING (nace_r2);


-- Q3 and Q4 by theme: one row per source, question, size and theme.
-- A theme can hold several reasons. Firms can tick more than one, so the
-- percentages must NOT be added up; the theme shows its highest reason.
CREATE OR REPLACE VIEW v_themes_eu_uk AS
WITH all_rows AS (
    SELECT 'EU' AS source, year, size_emp, indic_is, unit, value
    FROM stg_eurostat
    WHERE geo = 'EU27_2020'
      AND nace_r2 = 'C10-S951_X_K'
      AND ((indic_is LIKE 'E\_AI\_B%' ESCAPE '\' AND unit = 'PC_ENT_AI_EC')
        OR (indic_is LIKE 'E\_AI\_P%' ESCAPE '\' AND unit = 'PC_ENT_AI_TANY'))
    UNION ALL
    SELECT 'UK', year, size_emp, indic_is, unit, value
    FROM stg_ons
    WHERE nace_r2 = 'ALL'
),
latest AS (                              -- latest year per source
    SELECT * FROM all_rows
    QUALIFY year = MAX(year) OVER (PARTITION BY source)
),
themed AS (
    SELECT l.source, t.question, l.year, l.size_emp, t.theme, l.unit,
           MAX(l.value)  AS top_reason_pct,
           COUNT(*)      AS codes_in_theme
    FROM latest AS l
    JOIN dim_theme AS t
      ON t.code = l.indic_is
     AND t.source = CASE l.source WHEN 'EU' THEN 'eurostat' ELSE 'ons' END
    WHERE l.size_emp IN ('10-49', 'GE250')
    GROUP BY ALL
)
SELECT
    source, question, year, size_emp, theme, unit, top_reason_pct, codes_in_theme,
    -- "no barrier" (UK only) is kept for context but not ranked as a barrier
    CASE WHEN theme = 'no barrier' THEN NULL
         ELSE RANK() OVER (PARTITION BY source, question, size_emp, theme = 'no barrier'
                           ORDER BY top_reason_pct DESC)
    END AS theme_rank
FROM themed;
