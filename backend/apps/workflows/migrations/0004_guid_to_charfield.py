from django.db import migrations, models
import apps.core.db_fields


class Migration(migrations.Migration):
    """Change GUIDField (UUIDField) PKs to CharField(max_length=36) in all workflow models.

    Database columns are already varchar(36) — no DDL needed.
    This only updates Django's internal migration state.
    """

    dependencies = [
        ('workflows', '0003_switch_to_managed'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='workflowdefinition',
                    name='workflow_id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='workflowstep',
                    name='step_id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='workflowtransition',
                    name='transition_id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='stepaction',
                    name='action_id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='workflowinstance',
                    name='instance_id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='workflowtask',
                    name='task_id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='workflowauditlog',
                    name='log_id',
                    field=models.CharField(default=apps.core.db_fields.new_guid_str, max_length=36, primary_key=True, serialize=False),
                ),
            ],
            database_operations=[],
        ),
    ]
