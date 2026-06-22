from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("checklists", "0005_add_missing_fks"),
    ]

    operations = [
        # managed=False table — use RunSQL so we control when the column is added.
        # IF NOT EXISTS guards against the column already existing (e.g. added manually
        # or by a previous upload_example action that wrote directly to default_storage).
        migrations.RunSQL(
            sql="ALTER TABLE checklist_item ADD COLUMN IF NOT EXISTS example_file VARCHAR(500) NULL",
            reverse_sql="ALTER TABLE checklist_item DROP COLUMN IF EXISTS example_file",
        ),
        # Register the field in Django's migration state only (database_forwards is a no-op
        # because the RunSQL above already handled the schema change).
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="checklistitem",
                    name="example_file",
                    field=models.FileField(
                        blank=True,
                        null=True,
                        upload_to="checklist_examples/",
                        help_text="Uploaded image or PDF stored in cloud storage (R2). Takes precedence over example_url when set.",
                    ),
                ),
            ],
        ),
    ]
