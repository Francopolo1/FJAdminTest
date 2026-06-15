import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('financials', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='org',
            name='parent_org',
            field=models.ForeignKey(
                blank=True, null=True, db_column='parent_org_id',
                related_name='children', on_delete=django.db.models.deletion.SET_NULL,
                to='financials.org',
            ),
        ),
        migrations.AddField(
            model_name='foapalstring',
            name='fund',
            field=models.ForeignKey(
                db_column='fund_id', related_name='foapal_strings',
                on_delete=django.db.models.deletion.PROTECT, to='financials.fund',
            ),
        ),
        migrations.AddField(
            model_name='foapalstring',
            name='program',
            field=models.ForeignKey(
                blank=True, null=True, db_column='program_id', related_name='foapal_strings',
                on_delete=django.db.models.deletion.SET_NULL, to='financials.program',
            ),
        ),
        migrations.AddField(
            model_name='foapalstring',
            name='activity',
            field=models.ForeignKey(
                blank=True, null=True, db_column='activity_id', related_name='foapal_strings',
                on_delete=django.db.models.deletion.SET_NULL, to='financials.activity',
            ),
        ),
        migrations.AddField(
            model_name='foapalstring',
            name='account',
            field=models.ForeignKey(
                db_column='account_id', related_name='foapal_strings',
                on_delete=django.db.models.deletion.PROTECT, to='financials.account',
            ),
        ),
        migrations.AddField(
            model_name='foapalstring',
            name='org',
            field=models.ForeignKey(
                db_column='org_id', related_name='foapal_strings',
                on_delete=django.db.models.deletion.PROTECT, to='financials.org',
            ),
        ),
        migrations.AddField(
            model_name='foapalstring',
            name='location',
            field=models.ForeignKey(
                blank=True, null=True, db_column='location_id', related_name='foapal_strings',
                on_delete=django.db.models.deletion.SET_NULL, to='financials.location',
            ),
        ),
        migrations.AddField(
            model_name='transaction',
            name='fund',
            field=models.ForeignKey(
                blank=True, null=True, db_column='fund_id', related_name='transactions',
                on_delete=django.db.models.deletion.SET_NULL, to='financials.fund',
            ),
        ),
        migrations.AddField(
            model_name='transaction',
            name='program',
            field=models.ForeignKey(
                blank=True, null=True, db_column='program_id', related_name='transactions',
                on_delete=django.db.models.deletion.SET_NULL, to='financials.program',
            ),
        ),
        migrations.AddField(
            model_name='transaction',
            name='activity',
            field=models.ForeignKey(
                blank=True, null=True, db_column='activity_id', related_name='transactions',
                on_delete=django.db.models.deletion.SET_NULL, to='financials.activity',
            ),
        ),
        migrations.AddField(
            model_name='transaction',
            name='account',
            field=models.ForeignKey(
                blank=True, null=True, db_column='account_id', related_name='transactions',
                on_delete=django.db.models.deletion.SET_NULL, to='financials.account',
            ),
        ),
        migrations.AddField(
            model_name='transaction',
            name='org',
            field=models.ForeignKey(
                blank=True, null=True, db_column='org_id', related_name='transactions',
                on_delete=django.db.models.deletion.SET_NULL, to='financials.org',
            ),
        ),
        migrations.AddField(
            model_name='transaction',
            name='foapal_string',
            field=models.ForeignKey(
                db_column='foapal_string_id', related_name='transactions',
                on_delete=django.db.models.deletion.PROTECT, to='financials.foapalstring',
            ),
        ),
        migrations.AddField(
            model_name='transaction',
            name='location',
            field=models.ForeignKey(
                blank=True, null=True, db_column='location_id', related_name='transactions',
                on_delete=django.db.models.deletion.SET_NULL, to='financials.location',
            ),
        ),
        migrations.AddField(
            model_name='transactionsplit',
            name='foapal_string',
            field=models.ForeignKey(
                db_column='foapal_string_id', related_name='splits',
                on_delete=django.db.models.deletion.PROTECT, to='financials.foapalstring',
            ),
        ),
        migrations.AddField(
            model_name='transactionsplit',
            name='transaction',
            field=models.ForeignKey(
                db_column='transaction_id', related_name='splits',
                on_delete=django.db.models.deletion.CASCADE, to='financials.transaction',
            ),
        ),
    ]
