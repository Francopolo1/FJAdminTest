"""
Replace program_facilities.risk_assessment (VARCHAR 5 code) with
risk_assessment_levels_id (INT FK → risk_assessment_levels.id).

program_facilities is managed=False so all DDL is via RunSQL.
Steps:
  1. Drop the composite FK added in 0012 (code + pft_id).
  2. Drop the old risk_assessment VARCHAR column.
  3. Add risk_assessment_levels_id INT NULL with a simple FK.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_program_facility_risk_fk'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- 1. Drop composite FK from migration 0012
            ALTER TABLE program_facilities
            DROP CONSTRAINT IF EXISTS fk_pf_risk_assessment;

            -- 2. Drop old varchar column
            ALTER TABLE program_facilities
            DROP COLUMN IF EXISTS risk_assessment;

            -- 3. Add new integer FK column
            ALTER TABLE program_facilities
            ADD risk_assessment_levels_id INTEGER NULL
                REFERENCES risk_assessment_levels(id)
                ON DELETE SET NULL;
            """,
            reverse_sql="""
            ALTER TABLE program_facilities
            DROP CONSTRAINT IF EXISTS
                program_facilities_risk_assessment_levels_id_fkey;

            ALTER TABLE program_facilities
            DROP COLUMN IF EXISTS risk_assessment_levels_id;

            ALTER TABLE program_facilities
            ADD risk_assessment VARCHAR(5) NULL;
            """,
        ),
    ]
