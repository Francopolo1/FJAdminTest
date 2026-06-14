from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checklists', '0002_checklistitem_example_url'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='checklistresponse',
                    name='box_folder_url',
                    field=models.CharField(blank=True, help_text='Link to the Box.com documents folder for this response.', max_length=500, null=True),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE checklist_response ADD box_folder_url NVARCHAR(500) NULL",
                    reverse_sql="ALTER TABLE checklist_response DROP COLUMN box_folder_url",
                ),
            ],
        ),
    ]
