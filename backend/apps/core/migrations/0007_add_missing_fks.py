import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_userprofile_user_manager'),
        ('financials', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='programfacilitytype',
            name='facility_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.DO_NOTHING, to='core.facilitytype',
            ),
        ),
        migrations.AddField(
            model_name='programfacilitytype',
            name='program',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.DO_NOTHING, to='financials.program',
            ),
        ),
        migrations.AddField(
            model_name='programfacilitytypeactivity',
            name='specialtracking',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING,
                to='core.specialtracking',
            ),
        ),
        migrations.RemoveField(
            model_name='programfacilitytypeactivity',
            name='foapalstring_id',
        ),
        migrations.AddField(
            model_name='programfacilitytypeactivity',
            name='foapalstring',
            field=models.ForeignKey(
                db_column='foapalstring_id', related_name='program_facility_type_activities',
                on_delete=django.db.models.deletion.DO_NOTHING, to='financials.foapalstring',
            ),
        ),
        migrations.AddField(
            model_name='programfacilitytypeactivity',
            name='program_facility_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.DO_NOTHING, to='core.programfacilitytype',
            ),
        ),
        migrations.AddField(
            model_name='facility',
            name='location',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.DO_NOTHING, to='core.facilitylocation',
            ),
        ),
        migrations.AddField(
            model_name='programdistricts',
            name='program',
            field=models.ForeignKey(
                db_column='program_id', related_name='program_districts',
                on_delete=django.db.models.deletion.DO_NOTHING, to='financials.program',
            ),
        ),
        migrations.AddField(
            model_name='programfacility',
            name='program_district',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.DO_NOTHING, to='core.programdistricts',
            ),
        ),
        migrations.AddField(
            model_name='programfacility',
            name='facility',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.DO_NOTHING, to='core.facility',
            ),
        ),
        migrations.AddField(
            model_name='programfacility',
            name='program_facility_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.DO_NOTHING, to='core.programfacilitytype',
            ),
        ),
        migrations.AddField(
            model_name='userprogram',
            name='user',
            field=models.ForeignKey(
                db_column='user_id', related_name='user_programs',
                on_delete=django.db.models.deletion.CASCADE, to='core.authuser',
            ),
        ),
        migrations.AddField(
            model_name='userprogram',
            name='program',
            field=models.ForeignKey(
                db_column='program_id', related_name='user_programs',
                on_delete=django.db.models.deletion.CASCADE, to='financials.program',
            ),
        ),
        migrations.AddField(
            model_name='userprogramdistrict',
            name='program_district',
            field=models.ForeignKey(
                db_column='program_district_id', related_name='user_program_districts',
                on_delete=django.db.models.deletion.CASCADE, to='core.programdistricts',
            ),
        ),
        migrations.AddField(
            model_name='userprogramdistrict',
            name='user',
            field=models.ForeignKey(
                db_column='user_id', related_name='user_program_districts',
                on_delete=django.db.models.deletion.CASCADE, to='core.authuser',
            ),
        ),
    ]
