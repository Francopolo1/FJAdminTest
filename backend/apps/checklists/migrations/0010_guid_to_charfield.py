from django.db import migrations, models
import apps.core.db_fields


class Migration(migrations.Migration):
    """Change GUIDField (UUIDField) PKs to CharField(max_length=36) in all checklist models.

    Database columns are already varchar(36) — no DDL needed.
    This only updates Django's internal migration state.
    """

    dependencies = [
        ('checklists', '0009_remove_duplicate_compliance_rule_model'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='checklisttemplate',
                    name='template_id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='checklistitem',
                    name='item_id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='checklistrun',
                    name='run_id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='checklistresponse',
                    name='response_id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
            ],
            database_operations=[],
        ),
    ]
