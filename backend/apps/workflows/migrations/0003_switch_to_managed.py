from django.db import migrations


class Migration(migrations.Migration):
    """Switch all workflow models from managed=False to managed=True.

    Because the tables already exist in production, we use SeparateDatabaseAndState
    to update Django's internal state without running any DDL.
    """

    dependencies = [
        ('workflows', '0002_add_missing_fks'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterModelOptions(
                    name='workflowdefinition',
                    options={'ordering': [], 'unique_together': {('name', 'version')}},
                ),
                migrations.AlterModelOptions(
                    name='workflowstep',
                    options={'ordering': ['step_order']},
                ),
                migrations.AlterModelOptions(
                    name='workflowtransition',
                    options={'unique_together': {('from_step', 'trigger_event')}},
                ),
                migrations.AlterModelOptions(
                    name='workflowinstance',
                    options={'ordering': ['-started_at']},
                ),
                migrations.AlterModelOptions(
                    name='workflowtask',
                    options={'ordering': ['due_date']},
                ),
                migrations.AlterModelOptions(
                    name='workflowauditlog',
                    options={'ordering': ['-logged_at']},
                ),
                migrations.AlterModelOptions(
                    name='stepaction',
                    options={'ordering': ['execution_order']},
                ),
            ],
            database_operations=[],  # No DDL — tables already exist
        ),
    ]
