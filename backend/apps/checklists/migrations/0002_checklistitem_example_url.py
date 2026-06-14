from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checklists', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='checklistitem',
                    name='example_url',
                    field=models.CharField(blank=True, help_text='Link to an example of a correctly completed response for this item.', max_length=500, null=True),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE checklist_item ADD example_url NVARCHAR(500) NULL",
                    reverse_sql="ALTER TABLE checklist_item DROP COLUMN example_url",
                ),
            ],
        ),
    ]
