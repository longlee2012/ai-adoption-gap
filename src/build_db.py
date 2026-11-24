"""
Step 4: build the SQL model.

What it does:
  1. Creates (or rebuilds) the database file data/ai_gap.duckdb.
  2. Runs the SQL files in sql/ in order: staging tables, lookup tables, views.
  3. Runs the data tests in sql/04_tests.sql. Every test must return 0 rows.
  4. Exports each view to data/marts/<view>.csv for Python, Excel and Power BI.

Run it from the project folder (after combine.py):
    python src/build_db.py
"""

import sys
from pathlib import Path

import duckdb

PROJECT_DIR = Path(__file__).resolve().parent.parent
SQL_DIR = PROJECT_DIR / "sql"
DB_PATH = PROJECT_DIR / "data" / "ai_gap.duckdb"
MARTS_DIR = PROJECT_DIR / "data" / "marts"

BUILD_FILES = ["01_staging.sql", "02_dimensions.sql", "03_views.sql"]
TEST_FILE = "04_tests.sql"


def run_build(con: duckdb.DuckDBPyConnection) -> None:
    for name in BUILD_FILES:
        print(f"Running {name}...")
        con.execute((SQL_DIR / name).read_text(encoding="utf-8"))


def read_tests() -> list[tuple[str, str]]:
    """Split 04_tests.sql into (test name, query) pairs at each '-- test:' line."""
    tests, name, lines = [], None, []
    for line in (SQL_DIR / TEST_FILE).read_text(encoding="utf-8").splitlines():
        if line.startswith("-- test:"):
            if name:
                tests.append((name, "\n".join(lines)))
            name, lines = line.removeprefix("-- test:").strip(), []
        elif name and not line.startswith("--"):
            lines.append(line)
    if name:
        tests.append((name, "\n".join(lines)))
    return tests


def run_tests(con: duckdb.DuckDBPyConnection) -> bool:
    print("\nData tests:")
    all_passed = True
    for name, query in read_tests():
        problems = con.execute(query.strip().rstrip(";")).df()
        if problems.empty:
            print(f"  PASS  {name}")
        else:
            all_passed = False
            print(f"  FAIL  {name}  ({len(problems)} problem rows)")
            print(problems.head(5).to_string(index=False))
    return all_passed


def export_views(con: duckdb.DuckDBPyConnection) -> None:
    MARTS_DIR.mkdir(parents=True, exist_ok=True)
    views = con.execute(
        "SELECT view_name FROM duckdb_views() WHERE NOT internal ORDER BY view_name"
    ).fetchall()
    print("\nExported views:")
    for (view,) in views:
        out = MARTS_DIR / f"{view}.csv"
        con.execute(f"COPY {view} TO '{out.as_posix()}' (HEADER)")
        rows = con.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
        print(f"  {view}: {rows} rows -> data/marts/{out.name}")


def main() -> None:
    con = duckdb.connect(str(DB_PATH))
    # Relative paths in the SQL (data/clean/..., docs/...) are read from the project folder
    con.execute(f"SET file_search_path = '{PROJECT_DIR.as_posix()}'")
    run_build(con)
    if not run_tests(con):
        print("\nSome tests failed. Fix them before using the views.")
        sys.exit(1)
    export_views(con)
    con.close()
    print(f"\nDone. Database: {DB_PATH}")


if __name__ == "__main__":
    main()
