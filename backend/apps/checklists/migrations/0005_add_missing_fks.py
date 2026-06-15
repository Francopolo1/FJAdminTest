import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checklists', '0004_checklistitem_category'),
        ('compliance', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='checklistitemcompliancerules',
            name='checklist_item',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING,
                to='checklists.checklistitem',
            ),
        ),
        migrations.AddField(
            model_name='checklistitemcompliancerules',
            name='compliance_rule',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.DO_NOTHING, to='compliance.compliancerule',
            ),
        ),
    ]
