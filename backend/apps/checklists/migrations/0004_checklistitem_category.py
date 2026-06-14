from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checklists', '0003_checklistresponse_box_folder_url'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='checklistitem',
                    name='category',
                    field=models.CharField(blank=True, max_length=100, null=True),
                ),
                migrations.AlterModelOptions(
                    name='checklistitem',
                    options={'ordering': ['category', 'display_order']},
                ),
                migrations.AddIndex(
                    model_name='checklistitem',
                    index=models.Index(fields=['template', 'category', 'display_order'], name='idx_chkitem_tmpl_cat_order'),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE checklist_item ADD category NVARCHAR(100) NULL",
                    reverse_sql="ALTER TABLE checklist_item DROP COLUMN category",
                ),
            ],
        ),
    ]
