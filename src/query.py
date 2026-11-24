"""
Run any SQL query against the Step 4 database and print the result.

Use it to explore the views, or to practise SQL:
    python src/query.py "SELECT * FROM v_q1_gap_trend WHERE geo = 'EU27_2020'"
    python src/query.py sql/explore.sql

Run build_db.py first, so data/ai_gap.duckdb exists.
"""

import sys
from pathlib import Path

import duckdb

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "data" / "ai_gap.duckdb"


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        return
    arg = sys.argv[1]
    sql = Path(arg).read_text(encoding="utf-8") if arg.endswith(".sql") else arg
    con = duckdb.connect(str(DB_PATH), read_only=True)  # read-only: exploring can't break anything
    print(con.sql(sql).df().to_string(index=False, max_rows=50))


if __name__ == "__main__":
    main()
