from django.db import migrations, models
import apps.core.db_fields


class Migration(migrations.Migration):
    """Change GUIDField (UUIDField) PKs to CharField(max_length=36) in all financial models.

    Database columns are already varchar(36) — no DDL needed.
    This only updates Django's internal migration state.
    """

    dependencies = [
        ('financials', '0003_alter_account_options_alter_activity_options_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='fund',
                    name='fund_id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='org',
                    name='org_id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='account',
                    name='account_id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='activity',
                    name='activity_id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='location',
                    name='locaton_id',
                    field=models.CharField(db_column='locaton_id', default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='foapalstring',
                    name='foapalstring_id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='transaction',
                    name='id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='transactionsplit',
                    name='split_id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
            ],
            database_operations=[],
        ),
    ]
