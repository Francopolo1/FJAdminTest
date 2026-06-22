from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_step_type_roles'),
    ]

    operations = [
        migrations.AddField(
            model_name='programfacility',
            name='season_start',
            field=models.CharField(
                blank=True, null=True, max_length=5,
                help_text="Facility season start date as 'MM-DD' (e.g., '05-01' for May 1st). If set, activity_flag auto-adjusts based on season."
            ),
        ),
        migrations.AddField(
            model_name='programfacility',
            name='season_end',
            field=models.CharField(
                blank=True, null=True, max_length=5,
                help_text="Facility season end date as 'MM-DD' (e.g., '09-30' for Sept 30th). If set, activity_flag auto-adjusts based on season."
            ),
        ),
    ]
