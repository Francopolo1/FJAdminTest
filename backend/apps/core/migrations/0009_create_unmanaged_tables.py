"""
Creates user_programs and user_program_districts in PostgreSQL (Railway).
These models are managed=False so Django skips them in normal migrations.
The SeparateDatabaseAndState pattern runs DDL without touching Django state.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_authuser_groups_permissions'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE TABLE IF NOT EXISTS user_programs (
                        id                SERIAL          NOT NULL PRIMARY KEY,
                        user_id           INTEGER         NOT NULL
                            REFERENCES auth_user(id) ON DELETE CASCADE,
                        program_id        VARCHAR(36)     NOT NULL
                            REFERENCES programs(program_id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS user_program_districts (
                        auth_user_program_district_id   VARCHAR(36)             NOT NULL PRIMARY KEY,
                        user_id                         INTEGER                 NOT NULL
                            REFERENCES auth_user(id) ON DELETE CASCADE,
                        program_district_id             VARCHAR(36)             NOT NULL
                            REFERENCES program_districts(program_district_id) ON DELETE CASCADE,
                        assigned_date                   TIMESTAMP WITH TIME ZONE NOT NULL
                    );
                    """,
                    reverse_sql="""
                    DROP TABLE IF EXISTS user_program_districts;
                    DROP TABLE IF EXISTS user_programs;
                    """,
                ),
            ],
            state_operations=[],
        ),
    ]
