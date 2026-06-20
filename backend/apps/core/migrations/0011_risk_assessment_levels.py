import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_reset_sequences'),
    ]

    operations = [
        migrations.CreateModel(
            name='RiskAssessmentLevel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=5)),
                ('label', models.CharField(max_length=50)),
                ('visit_frequency_days', models.PositiveIntegerField(
                    help_text='Target days between visits for this risk level.',
                )),
                ('description', models.TextField(blank=True, null=True)),
                ('program_facility_type', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='risk_assessment_levels',
                    to='core.programfacilitytype',
                )),
            ],
            options={
                'verbose_name': 'risk assessment level',
                'verbose_name_plural': 'risk assessment levels',
                'db_table': 'risk_assessment_levels',
                'ordering': ['program_facility_type', 'visit_frequency_days'],
            },
        ),
        migrations.AddConstraint(
            model_name='riskassessmentlevel',
            constraint=models.UniqueConstraint(
                fields=['code', 'program_facility_type'],
                name='unique_risk_code_per_pft',
            ),
        ),
    ]
