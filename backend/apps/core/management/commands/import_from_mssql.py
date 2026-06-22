"""One-time data import: copy all rows from the local SQL Server
(FJADMINDBMODEL on JOHNSON_OFFICE) into the Postgres 'default' database.

Must be run from a machine with network access to JOHNSON_OFFICE, e.g.:

    venv\\Scripts\\python.exe manage.py import_from_mssql
    venv\\Scripts\\python.exe manage.py import_from_mssql --dry-run
    venv\\Scripts\\python.exe manage.py import_from_mssql --only facilities,orgs
"""

import datetime
import struct

import pyodbc
from decouple import config
from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connections
from psycopg2.extras import execute_values


class Command(BaseCommand):
    help = "Copy all rows from the local SQL Server database into Postgres."

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            help="Comma-separated list of db_table names to import (default: all).",
            default="",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without writing to Postgres.",
        )

    def handle(self, *args, **options):
        pg = connections["default"]
        if pg.vendor != "postgresql":
            self.stderr.write("default database is not Postgres (vendor=%s) - aborting" % pg.vendor)
            return

        only = {t.strip() for t in options["only"].split(",") if t.strip()}

        # Collect distinct db_tables for managed=False (mirrored) models.
        tables = []
        seen = set()
        table_models = {}
        for model in apps.get_models():
            if model._meta.managed is not False:
                continue
            db_table = model._meta.db_table
            table_models.setdefault(db_table, model)
            if db_table in seen:
                continue
            seen.add(db_table)
            if only and db_table not in only:
                continue
            tables.append(db_table)

        self.stdout.write("Tables to import: %d" % len(tables))

        mssql = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=%s;DATABASE=%s;UID=%s;PWD=%s;TrustServerCertificate=yes"
            % (
                config("DB_HOST", default="JOHNSON_OFFICE"),
                config("DB_NAME", default="FJADMINDBMODEL"),
                config("DB_USER", default="Mulesoft"),
                config("DB_PASSWORD", default="Mulesoft1"),
            )
        )
        def handle_datetimeoffset(raw):
            tup = struct.unpack("<6hI2h", raw)
            return datetime.datetime(
                tup[0], tup[1], tup[2], tup[3], tup[4], tup[5], tup[6] // 1000,
                datetime.timezone(datetime.timedelta(hours=tup[7], minutes=tup[8])),
            )

        mssql.add_output_converter(-155, handle_datetimeoffset)
        mssql_cur = mssql.cursor()

        pg_cur = pg.cursor()

        # Map table -> matched columns, fetched rows
        plan = {}
        for table in tables:
            mssql_cur.execute("SELECT TOP 0 * FROM dbo.[%s]" % table)
            mssql_cols = [c[0] for c in mssql_cur.description]

            pg_cur.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
                [table],
            )
            pg_cols = {r[0].lower(): r[0] for r in pg_cur.fetchall()}

            cols = [c for c in mssql_cols if c.lower() in pg_cols]
            pg_col_names = [pg_cols[c.lower()] for c in cols]
            if not cols:
                self.stdout.write("  %s: no matching columns - skipping" % table)
                continue

            col_list = ", ".join("[%s]" % c for c in cols)
            mssql_cur.execute("SELECT %s FROM dbo.[%s]" % (col_list, table))
            rows = mssql_cur.fetchall()
            rows = [list(row) for row in rows]

            model = table_models.get(table)

            pg_cur.execute(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_name = %s AND is_nullable = 'NO' AND column_default IS NULL",
                [table],
            )
            not_null_types = dict(pg_cur.fetchall())
            not_null_cols = list(not_null_types)

            GENERIC_DEFAULTS = {
                "integer": 0, "bigint": 0, "smallint": 0,
                "numeric": 0, "double precision": 0, "real": 0,
                "boolean": False,
                "character varying": "", "text": "", "character": "",
            }

            def field_default(col):
                if model:
                    for field in model._meta.fields:
                        if field.column == col:
                            value = field.get_default()
                            if value is not None:
                                return value
                            break
                return GENERIC_DEFAULTS.get(not_null_types.get(col))

            # Required Postgres columns absent from the source: fill with the
            # model field's default (e.g. counters that are computed at runtime).
            matched = {c.lower() for c in cols}
            for col in not_null_cols:
                if col.lower() in matched:
                    continue
                default = field_default(col)
                pg_col_names.append(col)
                for row in rows:
                    row.append(default)

            # Source NULLs in NOT NULL Postgres columns: fall back to the
            # model field's default rather than violating the constraint.
            not_null_idx = {
                i: pg_col_names[i]
                for i in range(len(pg_col_names))
                if pg_col_names[i] in not_null_cols
            }
            for row in rows:
                for i, col in not_null_idx.items():
                    if row[i] is None:
                        row[i] = field_default(col)

            plan[table] = (pg_col_names, [tuple(row) for row in rows])
            self.stdout.write("  %s: %d rows, %d columns" % (table, len(rows), len(cols)))

        if options["dry_run"]:
            self.stdout.write("Dry run - no changes made.")
            return

        pg_cur.execute("SET session_replication_role = replica;")
        try:
            for table, (cols, rows) in plan.items():
                pg_cur.execute('DELETE FROM "%s"' % table)

            for table, (cols, rows) in plan.items():
                if not rows:
                    continue
                col_list = ", ".join('"%s"' % c for c in cols)
                sql = 'INSERT INTO "%s" (%s) VALUES %%s' % (table, col_list)
                execute_values(pg_cur, sql, rows)
                self.stdout.write("  inserted %d rows into %s" % (len(rows), table))

            # Reset sequences for serial/identity primary keys.
            for table, (cols, rows) in plan.items():
                pg_cur.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = %s AND column_default LIKE 'nextval%%'",
                    [table],
                )
                for (col,) in pg_cur.fetchall():
                    pg_cur.execute(
                        "SELECT setval(pg_get_serial_sequence(%s, %s), "
                        "COALESCE((SELECT MAX(\"%s\") FROM \"%s\"), 1))"
                        % ("%s", "%s", col, table),
                        [table, col],
                    )
        finally:
            pg_cur.execute("SET session_replication_role = DEFAULT;")

        pg.connection.commit()
        self.stdout.write(self.style.SUCCESS("Import complete."))
