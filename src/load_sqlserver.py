"""
Load the project's data into the local SQL Server (SQLEXPRESS).

What it does:
  1. Creates the database AIGap on localhost\\SQLEXPRESS if it does not exist.
  2. Creates three schemas: clean, marts, ref.
  3. Loads every CSV as a table (each run replaces the tables):
       data/clean/*.csv  -> clean.<file name>
       data/marts/*.csv  -> marts.<file name>
       docs/*.csv        -> ref.<file name>

Run it from the project folder (after build_db.py):
    python src/load_sqlserver.py

Then in VS Code: SQL Server panel -> SQLEXPRESS local -> Databases -> AIGap.
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

PROJECT_DIR = Path(__file__).resolve().parent.parent
SERVER = r"localhost\SQLEXPRESS"
DATABASE = "AIGap"
DRIVER = "ODBC Driver 17 for SQL Server"

FOLDERS = {
    "clean": PROJECT_DIR / "data" / "clean",
    "marts": PROJECT_DIR / "data" / "marts",
    "ref": PROJECT_DIR / "docs",
}


def engine_for(database: str):
    url = (
        f"mssql+pyodbc://@{SERVER}/{database}"
        f"?driver={DRIVER.replace(' ', '+')}&trusted_connection=yes"
    )
    return create_engine(url, fast_executemany=True)


def create_database() -> None:
    # CREATE DATABASE cannot run inside a transaction, so use autocommit
    with engine_for("master").connect().execution_options(
        isolation_level="AUTOCOMMIT"
    ) as con:
        con.execute(text(f"IF DB_ID('{DATABASE}') IS NULL CREATE DATABASE [{DATABASE}]"))


def main() -> None:
    create_database()
    engine = engine_for(DATABASE)

    with engine.begin() as con:
        for schema in FOLDERS:
            con.execute(text(
                f"IF SCHEMA_ID('{schema}') IS NULL EXEC('CREATE SCHEMA [{schema}]')"
            ))

    for schema, folder in FOLDERS.items():
        for csv in sorted(folder.glob("*.csv")):
            df = pd.read_csv(csv)
            df.to_sql(csv.stem, engine, schema=schema, if_exists="replace",
                      index=False, chunksize=1000)
            print(f"  {schema}.{csv.stem}: {len(df)} rows")

    print(f"\nDone. Database [{DATABASE}] on {SERVER}")


if __name__ == "__main__":
    main()
