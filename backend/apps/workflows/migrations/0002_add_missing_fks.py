import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflowdefinition',
            name='program_facility_type_activity',
            field=models.ForeignKey(
                db_column='program_facility_type_activity_id',
                on_delete=django.db.models.deletion.PROTECT, to='core.programfacilitytypeactivity',
            ),
        ),
        migrations.AddField(
            model_name='workflowstep',
            name='workflow',
            field=models.ForeignKey(
                db_column='workflow_id', related_name='steps',
                on_delete=django.db.models.deletion.CASCADE, to='workflows.workflowdefinition',
            ),
        ),
        migrations.AddField(
            model_name='workflowtransition',
            name='workflow',
            field=models.ForeignKey(
                db_column='workflow_id', related_name='transitions',
                on_delete=django.db.models.deletion.CASCADE, to='workflows.workflowdefinition',
            ),
        ),
        migrations.AddField(
            model_name='workflowtransition',
            name='from_step',
            field=models.ForeignKey(
                db_column='from_step_id', related_name='outgoing',
                on_delete=django.db.models.deletion.CASCADE, to='workflows.workflowstep',
            ),
        ),
        migrations.AddField(
            model_name='workflowtransition',
            name='to_step',
            field=models.ForeignKey(
                db_column='to_step_id', related_name='incoming',
                on_delete=django.db.models.deletion.CASCADE, to='workflows.workflowstep',
            ),
        ),
        migrations.AddField(
            model_name='stepaction',
            name='step',
            field=models.ForeignKey(
                db_column='step_id', related_name='actions',
                on_delete=django.db.models.deletion.CASCADE, to='workflows.workflowstep',
            ),
        ),
        migrations.AddField(
            model_name='workflowinstance',
            name='program_facility',
            field=models.ForeignKey(
                db_column='program_facility_id', related_name='instances',
                on_delete=django.db.models.deletion.PROTECT, to='core.programfacility',
            ),
        ),
        migrations.AddField(
            model_name='workflowinstance',
            name='workflow',
            field=models.ForeignKey(
                db_column='workflow_id', related_name='instances',
                on_delete=django.db.models.deletion.PROTECT, to='workflows.workflowdefinition',
            ),
        ),
        migrations.AddField(
            model_name='workflowinstance',
            name='current_step',
            field=models.ForeignKey(
                blank=True, null=True, db_column='current_step_id',
                on_delete=django.db.models.deletion.SET_NULL, to='workflows.workflowstep',
            ),
        ),
        migrations.AddField(
            model_name='workflowinstance',
            name='initiated_by',
            field=models.ForeignKey(
                db_column='initiated_by_id', related_name='initiated_instances',
                on_delete=django.db.models.deletion.PROTECT, to='core.authuser',
            ),
        ),
        migrations.AddField(
            model_name='workflowtask',
            name='step',
            field=models.ForeignKey(
                db_column='step_id', related_name='tasks',
                on_delete=django.db.models.deletion.PROTECT, to='workflows.workflowstep',
            ),
        ),
        migrations.AddField(
            model_name='workflowtask',
            name='assigned_to',
            field=models.ForeignKey(
                db_column='assigned_to', related_name='assigned_tasks',
                on_delete=django.db.models.deletion.PROTECT, to='core.authuser',
            ),
        ),
        migrations.AddField(
            model_name='workflowtask',
            name='delegated_to',
            field=models.ForeignKey(
                blank=True, null=True, db_column='delegated_to', related_name='delegated_tasks',
                on_delete=django.db.models.deletion.SET_NULL, to='core.authuser',
            ),
        ),
        migrations.AddField(
            model_name='workflowtask',
            name='assigned_by',
            field=models.ForeignKey(
                db_column='assigned_by', related_name='created_tasks',
                on_delete=django.db.models.deletion.PROTECT, to='core.authuser',
            ),
        ),
        migrations.AddField(
            model_name='workflowtask',
            name='instance',
            field=models.ForeignKey(
                db_column='instance_id', related_name='tasks',
                on_delete=django.db.models.deletion.CASCADE, to='workflows.workflowinstance',
            ),
        ),
        migrations.AddField(
            model_name='workflowauditlog',
            name='instance',
            field=models.ForeignKey(
                db_column='instance_id', related_name='audit_logs',
                on_delete=django.db.models.deletion.CASCADE, to='workflows.workflowinstance',
            ),
        ),
        migrations.AddField(
            model_name='workflowauditlog',
            name='actor',
            field=models.ForeignKey(
                db_column='actor_id', related_name='workflow_audit_logs',
                on_delete=django.db.models.deletion.PROTECT, to='core.authuser',
            ),
        ),
        migrations.AddField(
            model_name='workflowauditlog',
            name='task',
            field=models.ForeignKey(
                blank=True, null=True, db_column='task_Id',
                on_delete=django.db.models.deletion.SET_NULL, to='workflows.workflowtask',
            ),
        ),
    ]
