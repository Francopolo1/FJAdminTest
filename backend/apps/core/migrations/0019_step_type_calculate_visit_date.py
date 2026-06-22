from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_alter_auditlog_options_alter_authuser_options_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            INSERT INTO workflow_step_type_roles (step_type, label, responsible_role, description)
            VALUES (
                'CalculateVisitDate',
                'Calculate Visit Date',
                NULL,
                'Automated: recalculates program_facility.next_visit_date from the latest checklist run. Auto-advances.'
            )
            ON CONFLICT (step_type) DO NOTHING;
            """,
            reverse_sql="DELETE FROM workflow_step_type_roles WHERE step_type = 'CalculateVisitDate';",
        ),
    ]
