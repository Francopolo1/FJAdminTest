# Adds the `user` and `manager` FK fields that exist on the UserProfile
# model (and on the real dbo.user_profile table) but were missing from
# 0003_userprofile's CreateModel.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_seed_user_roles'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='user',
            field=models.OneToOneField(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                db_column='user_id',
                related_name='profile',
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='manager',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                db_column='manager_id',
                related_name='direct_reports',
                to='core.userprofile',
            ),
        ),
    ]
