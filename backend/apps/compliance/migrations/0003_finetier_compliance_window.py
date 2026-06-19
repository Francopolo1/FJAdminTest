from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("compliance", "0002_add_missing_fks"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE fine_tiers ADD COLUMN IF NOT EXISTS compliance_window INTEGER NULL",
            reverse_sql="ALTER TABLE fine_tiers DROP COLUMN IF EXISTS compliance_window",
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="finetier",
                    name="compliance_window",
                    field=models.IntegerField(
                        null=True,
                        blank=True,
                        help_text="Number of days in the compliance range for this tier.",
                    ),
                ),
            ],
        ),
    ]
