# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0010_auto_20151125_1340'),
    ]

    operations = [
        migrations.RenameField(
            model_name='searchset',
            old_name='ss_name',
            new_name='job_name',
        ),
        migrations.AlterUniqueTogether(
            name='searchset',
            unique_together=set([('user_id', 'job_name')]),
        ),
    ]
