from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_program_facility_seasonality'),
    ]

    operations = [
        migrations.AddField(
            model_name='programfacility',
            name='next_visit_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='programfacility',
            name='visit_month_seed',
            field=models.SmallIntegerField(
                blank=True, null=True,
                help_text="Preferred month for facility visits (1-12, where 1=January, 12=December). If set, next_visit_date aligns to this month. Combined with risk_assessment_level.visit_frequency_days to schedule visits."
            ),
        ),
    ]
