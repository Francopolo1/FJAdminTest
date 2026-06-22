"""
Add composite FK from program_facilities(risk_assessment, program_facility_type_id)
to risk_assessment_levels(code, program_facility_type_id).

program_facilities is managed=False (legacy table) so the constraint is applied
via RunSQL.  NOT VALID skips checking existing rows — only new inserts/updates
are enforced, avoiding failures on pre-existing data that predates the lookup table.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_risk_assessment_levels'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE program_facilities
            ADD CONSTRAINT fk_pf_risk_assessment
                FOREIGN KEY (risk_assessment, program_facility_type_id)
                REFERENCES risk_assessment_levels (code, program_facility_type_id)
                ON UPDATE CASCADE
                ON DELETE SET NULL
                NOT VALID;
            """,
            reverse_sql="""
            ALTER TABLE program_facilities
            DROP CONSTRAINT IF EXISTS fk_pf_risk_assessment;
            """,
        ),
    ]
