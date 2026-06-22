"""
compare_schemas.py
==================
Compares the local MSSQL database schema against the Railway PostgreSQL
database schema and reports:

  - Tables only in MSSQL
  - Tables only in PostgreSQL
  - Tables in both but with column differences (missing columns, type mismatches)

Usage (from backend/ with venv active):
    python compare_schemas.py

The script reads connection details from .env via python-decouple, the same
way Django does.
"""

import sys
import pyodbc
import psycopg2
from decouple import config

# ── Connection helpers ────────────────────────────────────────────────────────

def mssql_conn():
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={config('DB_HOST', default='JOHNSON_OFFICE')},{config('DB_PORT', default='1433')};"
        f"DATABASE={config('DB_NAME', default='FJADMINDBMODEL')};"
        f"UID={config('DB_USER', default='Mulesoft')};"
        f"PWD={config('DB_PASSWORD', default='Mulesoft1')};"
        f"TrustServerCertificate=yes;"
    )

def pg_conn():
    return psycopg2.connect(config("DATABASE_URL"))


# ── Schema introspection ───────────────────────────────────────────────────────

def get_mssql_schema(conn):
    """Returns {table: {col: normalized_type}} for all user tables."""
    cur = conn.cursor()
    cur.execute("""
        SELECT
            t.name                          AS table_name,
            c.name                          AS column_name,
            tp.name                         AS type_name,
            c.max_length,
            c.is_nullable
        FROM sys.tables t
        JOIN sys.columns c  ON c.object_id = t.object_id
        JOIN sys.types  tp  ON tp.user_type_id = c.user_type_id
        WHERE t.is_ms_shipped = 0
        ORDER BY t.name, c.column_id
    """)
    schema = {}
    for table, col, type_name, max_length, nullable in cur.fetchall():
        schema.setdefault(table, {})[col] = {
            "type": type_name.lower(),
            "nullable": bool(nullable),
        }
    return schema

def get_pg_schema(conn):
    """Returns {table: {col: normalized_type}} for all non-system tables."""
    cur = conn.cursor()
    cur.execute("""
        SELECT
            table_name,
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """)
    schema = {}
    for table, col, data_type, nullable in cur.fetchall():
        schema.setdefault(table, {})[col] = {
            "type": data_type.lower(),
            "nullable": nullable == "YES",
        }
    return schema


# ── Type normalisation ─────────────────────────────────────────────────────────
# MSSQL and PostgreSQL use different type names for the same concept.
# Map both to a canonical name so we can compare apples to apples.

TYPE_MAP = {
    # MSSQL → canonical
    "nvarchar":           "varchar",
    "varchar":            "varchar",
    "nchar":              "char",
    "char":               "char",
    "ntext":              "text",
    "text":               "text",
    "int":                "integer",
    "bigint":             "bigint",
    "smallint":           "smallint",
    "tinyint":            "smallint",
    "bit":                "boolean",
    "float":              "float",
    "real":               "float",
    "decimal":            "numeric",
    "numeric":            "numeric",
    "money":              "numeric",
    "smallmoney":         "numeric",
    "datetime":           "timestamp",
    "datetime2":          "timestamp",
    "smalldatetime":      "timestamp",
    "date":               "date",
    "time":               "time",
    "uniqueidentifier":   "uuid",
    "varbinary":          "bytea",
    "image":              "bytea",
    "xml":                "text",
    # PostgreSQL → canonical
    "character varying":  "varchar",
    "character":          "char",
    "integer":            "integer",
    "boolean":            "boolean",
    "double precision":   "float",
    "timestamp without time zone": "timestamp",
    "timestamp with time zone":    "timestamp",
    "uuid":               "uuid",
    "bytea":              "bytea",
    "jsonb":              "json",
    "json":               "json",
    "user-defined":       "uuid",  # Postgres sometimes shows uuid custom types this way
}

def normalise(t):
    return TYPE_MAP.get(t.lower(), t.lower())


# ── Diff ──────────────────────────────────────────────────────────────────────

def diff_schemas(mssql, pg):
    mssql_tables = set(mssql)
    pg_tables    = set(pg)

    only_mssql = sorted(mssql_tables - pg_tables)
    only_pg    = sorted(pg_tables - mssql_tables)
    common     = sorted(mssql_tables & pg_tables)

    column_diffs = {}
    for table in common:
        ms_cols = mssql[table]
        pg_cols = pg[table]
        ms_names = set(ms_cols)
        pg_names = set(pg_cols)

        diffs = []

        for col in sorted(ms_names - pg_names):
            diffs.append(f"  MSSQL only : {col} ({ms_cols[col]['type']})")

        for col in sorted(pg_names - ms_names):
            diffs.append(f"  PG only    : {col} ({pg_cols[col]['type']})")

        for col in sorted(ms_names & pg_names):
            ms_type = normalise(ms_cols[col]["type"])
            pg_type = normalise(pg_cols[col]["type"])
            if ms_type != pg_type:
                diffs.append(f"  TYPE DIFF  : {col}  MSSQL={ms_type}  PG={pg_type}")

        if diffs:
            column_diffs[table] = diffs

    return only_mssql, only_pg, column_diffs


# ── Report ────────────────────────────────────────────────────────────────────

def main():
    print("Connecting to MSSQL...", end=" ", flush=True)
    try:
        ms = mssql_conn()
        print("OK")
    except Exception as e:
        print(f"FAILED\n  {e}")
        sys.exit(1)

    print("Connecting to PostgreSQL...", end=" ", flush=True)
    try:
        pg = pg_conn()
        print("OK")
    except Exception as e:
        print(f"FAILED\n  {e}")
        sys.exit(1)

    print("\nIntrospecting schemas...")
    mssql_schema = get_mssql_schema(ms)
    pg_schema    = get_pg_schema(pg)

    print(f"  MSSQL tables : {len(mssql_schema)}")
    print(f"  PG tables    : {len(pg_schema)}")

    only_mssql, only_pg, column_diffs = diff_schemas(mssql_schema, pg_schema)

    print("\n" + "="*60)

    if only_mssql:
        print(f"\n[TABLES ONLY IN MSSQL] ({len(only_mssql)})")
        for t in only_mssql:
            print(f"  {t}")

    if only_pg:
        print(f"\n[TABLES ONLY IN POSTGRESQL] ({len(only_pg)})")
        for t in only_pg:
            print(f"  {t}")

    if column_diffs:
        print(f"\n[COLUMN DIFFERENCES IN SHARED TABLES] ({len(column_diffs)} tables)")
        for table, diffs in column_diffs.items():
            print(f"\n  {table}")
            for d in diffs:
                print(f"  {d}")

    if not only_mssql and not only_pg and not column_diffs:
        print("\n✓ Schemas are identical (after type normalisation).")
    else:
        total = len(only_mssql) + len(only_pg) + len(column_diffs)
        print(f"\n{total} difference(s) found.")

    ms.close()
    pg.close()


if __name__ == "__main__":
    main()
