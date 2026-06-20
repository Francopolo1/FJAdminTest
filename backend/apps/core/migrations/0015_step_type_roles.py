from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_activity_flags'),
    ]

    operations = [
        migrations.CreateModel(
            name='StepTypeRole',
            fields=[
                ('step_type',        models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('label',            models.CharField(max_length=100)),
                ('responsible_role', models.CharField(
                    max_length=30, null=True, blank=True,
                    help_text='UserProfile.role that handles this step. Leave blank for automated steps.',
                )),
                ('description',      models.TextField(null=True, blank=True)),
            ],
            options={
                'verbose_name':        'step type role',
                'verbose_name_plural': 'step type roles',
                'db_table':            'workflow_step_type_roles',
                'ordering':            ['step_type'],
            },
        ),

        migrations.RunSQL(
            sql="""
            INSERT INTO workflow_step_type_roles (step_type, label, responsible_role, description)
            VALUES
                ('Manual',          'Manual',           'inspector',  'Inspectors complete manual field steps.'),
                ('Decision',        'Decision',         'supervisor', 'Supervisors approve or reject decisions.'),
                ('ComplianceCheck', 'Compliance Check', NULL,         'Automated: assesses fines from violations. Auto-advances.'),
                ('Automated',       'Automated',        NULL,         'Generic automated step. Auto-advances via the Auto trigger.')
            ON CONFLICT (step_type) DO NOTHING;
            """,
            reverse_sql="DELETE FROM workflow_step_type_roles WHERE step_type IN ('Manual','Decision','ComplianceCheck','Automated');",
        ),
    ]
