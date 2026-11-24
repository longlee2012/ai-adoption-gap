-- =====================================================================
-- 02_dimensions.sql
-- Lookup tables that turn codes into readable labels.
--
-- Why: the data says "10-49" and "E_AI_BLE". A dashboard must say
-- "Small (10-49)" and "Lack of expertise". Keeping labels in ONE table
-- means a label is fixed in one place, not in every chart.
-- =====================================================================

-- Size groups, with a sort order so charts show small -> large, not A-Z
CREATE OR REPLACE TABLE dim_size AS
SELECT * FROM (VALUES
    ('0-9',     'Micro (0-9)',             0, FALSE),
    ('10-49',   'Small (10-49)',           1, TRUE),
    ('50-249',  'Medium (50-249)',         2, TRUE),
    ('50-99',   'Medium (50-99), UK only',   3, FALSE),
    ('100-249', 'Medium (100-249), UK only', 4, FALSE),
    ('GE250',   'Large (250+)',            5, TRUE),
    ('10-249',  'SMEs (10-249)',           6, FALSE),
    ('GE10',    'All firms (10+)',         7, FALSE)
) AS t(size_emp, size_label, sort_order, is_main_group);

-- Sectors (NACE sections kept in Step 2)
CREATE OR REPLACE TABLE dim_sector AS
SELECT * FROM (VALUES
    ('C10-S951_X_K', 'All sectors'),
    ('C',    'Manufacturing'),
    ('D',    'Electricity and gas'),
    ('E',    'Water and waste'),
    ('F',    'Construction'),
    ('G',    'Wholesale and retail'),
    ('H',    'Transport and storage'),
    ('I',    'Accommodation and food'),
    ('J',    'Information and communication'),
    ('L',    'Real estate'),
    ('M',    'Professional and scientific'),
    ('N',    'Administrative and support'),
    ('S951', 'Repair of computers'),
    ('S',    'Other services (UK, all of S)')
) AS t(nace_r2, sector_label);

-- Every Eurostat code with its official label, from docs/codebook.csv.
-- The same code appears once per dataset, so keep one row per code.
CREATE OR REPLACE TABLE dim_code AS
SELECT
    "column"                         AS dimension,
    code,
    any_value(official_label)        AS official_label,
    any_value(plain_english)         AS plain_english
FROM read_csv('docs/codebook.csv', header = true, all_varchar = true)
GROUP BY "column", code;

-- Shared themes from Step 3 (docs/theme_map.csv). EU and UK questions are worded
-- differently, so they are compared through a common theme, e.g. "skills".
CREATE OR REPLACE TABLE dim_theme AS
SELECT source, question, code, label, theme
FROM read_csv('docs/theme_map.csv', header = true, all_varchar = true);
