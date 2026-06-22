"""
Reset PostgreSQL sequences for tables whose data was imported from MSSQL,
so auto-increment PKs don't collide with existing rows.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_create_unmanaged_tables'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            SELECT setval('user_programs_id_seq',
                COALESCE((SELECT MAX(id) FROM user_programs), 0));
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
