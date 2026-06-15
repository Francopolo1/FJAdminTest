import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compliance', '0001_initial'),
        ('checklists', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='fineschedule',
            name='compliance_rule',
            field=models.ForeignKey(
                db_column='compliance_rule_id', related_name='fine_schedules',
                on_delete=django.db.models.deletion.PROTECT, to='compliance.compliancerule',
            ),
        ),
        migrations.AddField(
            model_name='finetier',
            name='violation_severity_level',
            field=models.ForeignKey(
                db_column='violation_severity_level_id', related_name='fine_tiers',
                on_delete=django.db.models.deletion.PROTECT, to='compliance.violationseveritylevel',
            ),
        ),
        migrations.AddField(
            model_name='finetier',
            name='fine_schedule',
            field=models.ForeignKey(
                db_column='fine_schedule_id', related_name='tiers',
                on_delete=django.db.models.deletion.CASCADE, to='compliance.fineschedule',
            ),
        ),
        migrations.AddField(
            model_name='checklistitemcompliancerule',
            name='checklist_item',
            field=models.ForeignKey(
                null=True, db_column='checklist_item_id', related_name='compliance_rules',
                on_delete=django.db.models.deletion.SET_NULL, to='checklists.checklistitem',
            ),
        ),
        migrations.AddField(
            model_name='checklistitemcompliancerule',
            name='compliance_rule',
            field=models.ForeignKey(
                db_column='compliance_rule_id', related_name='checklist_item_links',
                on_delete=django.db.models.deletion.PROTECT, to='compliance.compliancerule',
            ),
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='complianceviolation',
                    name='checklist_item_compliance_rule',
                    field=models.ForeignKey(
                        db_column='checklist_item_compliance_rule_id', related_name='violations',
                        on_delete=django.db.models.deletion.PROTECT, to='compliance.checklistitemcompliancerule',
                    ),
                ),
            ],
            database_operations=[
                migrations.AddField(
                    model_name='complianceviolation',
                    name='checklist_item_compliance_rule',
                    field=models.CharField(max_length=36, db_column='checklist_item_compliance_rule_id', default=''),
                    preserve_default=False,
                ),
            ],
        ),
        migrations.AddField(
            model_name='complianceviolation',
            name='checklist_response',
            field=models.ForeignKey(
                db_column='checklist_response_id', related_name='violations',
                on_delete=django.db.models.deletion.PROTECT, to='checklists.checklistresponse',
            ),
        ),
        migrations.AddField(
            model_name='complianceviolation',
            name='violation_severity_level',
            field=models.ForeignKey(
                db_column='violation_severity_level_id', related_name='violations',
                on_delete=django.db.models.deletion.PROTECT, to='compliance.violationseveritylevel',
            ),
        ),
    ]
