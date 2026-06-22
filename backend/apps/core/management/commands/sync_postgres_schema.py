"""Create the FJAdminDBModel schema (mirrored from SQL Server) on Postgres.

All app models are declared with `managed = False` because the original
schema lives in SQL Server. When `default` points at Postgres, this command
temporarily treats those models as managed so `migrate` creates matching
tables, and strips SQL Server-only `db_collation` values (e.g.
"SQL_Latin1_General_CP1_CI_AS") which are not valid Postgres collations.

Usage: python manage.py sync_postgres_schema
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.operations.models import CreateModel
from django.db.migrations.operations.special import RunSQL, SeparateDatabaseAndState


class Command(BaseCommand):
    help = "Create tables for managed=False models on the Postgres 'default' database."

    def handle(self, *args, **options):
        connection = connections["default"]
        if connection.vendor != "postgresql":
            self.stderr.write(
                "default database is not Postgres (vendor=%s) - aborting"
                % connection.vendor
            )
            return

        loader = MigrationLoader(connection)
        patched_models = 0
        patched_fields = 0
        seen_tables = set()

        for migration in loader.disk_migrations.values():
            for op in migration.operations:
                if isinstance(op, SeparateDatabaseAndState):
                    # Replace SQL Server-specific RunSQL (e.g. NVARCHAR
                    # ALTER TABLE) with the backend-appropriate operations
                    # derived from state. Operations with their own
                    # Postgres-compatible database_operations are left as-is.
                    if any(isinstance(o, RunSQL) for o in op.database_operations):
                        op.database_operations = op.state_operations
                    continue
                if not isinstance(op, CreateModel):
                    continue
                if op.options.get("managed") is False:
                    db_table = op.options.get("db_table", op.name.lower())
                    if db_table in seen_tables:
                        # Same underlying table modeled (unmanaged) by more
                        # than one app - only create it once.
                        continue
                    seen_tables.add(db_table)
                    op.options["managed"] = True
                    patched_models += 1
                for _name, field in op.fields:
                    if getattr(field, "db_collation", None):
                        field.db_collation = None
                        patched_fields += 1

        self.stdout.write(
            "Patched %d model(s) to managed=True and stripped %d collation(s)"
            % (patched_models, patched_fields)
        )

        call_command("migrate", database="default", verbosity=2)
