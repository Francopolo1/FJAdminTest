from django.db import migrations


class Migration(migrations.Migration):
    """Remove the duplicate ChecklistItemComplianceRules model from the
    checklists app. The compliance app's ChecklistItemComplianceRule model
    (managed=False) is the authoritative owner of the checklist_item_compliance_rules
    table and already provides the compliance_rules reverse relation on ChecklistItem.

    This migration only removes the model from Django's state — no DDL is run
    because managed was False and the table is owned by the compliance app.
    """

    dependencies = [
        ('checklists', '0008_alter_checklistitemcompliancerules_options'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name='ChecklistItemComplianceRules'),
            ],
            database_operations=[],  # Table stays — owned by compliance app
        ),
    ]
