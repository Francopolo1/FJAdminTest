from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_program_facility_risk_fk_int'),
    ]

    operations = [
        # Create the lookup table
        migrations.CreateModel(
            name='ActivityFlag',
            fields=[
                ('code',        models.CharField(max_length=1, primary_key=True, serialize=False)),
                ('label',       models.CharField(max_length=50)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name':        'activity flag',
                'verbose_name_plural': 'activity flags',
                'db_table':            'activity_flags',
                'ordering':            ['code'],
            },
        ),

        # Seed the three standard values
        migrations.RunSQL(
            sql="""
            INSERT INTO activity_flags (code, label, description)
            VALUES
                ('A', 'Active',   'Facility is currently active and subject to visits.'),
                ('I', 'Inactive', 'Facility is temporarily inactive.'),
                ('C', 'Closed',   'Facility is permanently closed.')
            ON CONFLICT (code) DO NOTHING;
            """,
            reverse_sql="DELETE FROM activity_flags WHERE code IN ('A', 'I', 'C');",
        ),

        # Add FK constraint on program_facilities.activity_flag → activity_flags.code
        # NOT VALID skips existing row check; new writes are enforced.
        migrations.RunSQL(
            sql="""
            ALTER TABLE program_facilities
            ADD CONSTRAINT fk_pf_activity_flag
                FOREIGN KEY (activity_flag)
                REFERENCES activity_flags (code)
                ON UPDATE CASCADE
                ON DELETE SET NULL
                NOT VALID;
            """,
            reverse_sql="""
            ALTER TABLE program_facilities
            DROP CONSTRAINT IF EXISTS fk_pf_activity_flag;
            """,
        ),
    ]
