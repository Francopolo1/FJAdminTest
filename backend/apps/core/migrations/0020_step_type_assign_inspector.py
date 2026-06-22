from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_step_type_calculate_visit_date'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            INSERT INTO workflow_step_type_roles (step_type, label, responsible_role, description)
            VALUES (
                'AssignInspector',
                'Assign Inspector',
                NULL,
                'Automated: creates a task assigned to the district inspector(s) for this facility, then auto-advances.'
            )
            ON CONFLICT (step_type) DO NOTHING;
            """,
            reverse_sql="DELETE FROM workflow_step_type_roles WHERE step_type = 'AssignInspector';",
        ),
    ]
