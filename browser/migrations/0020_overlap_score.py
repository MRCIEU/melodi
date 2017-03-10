# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0019_meshcompare_job_progress'),
    ]

    operations = [
        migrations.AddField(
            model_name='overlap',
            name='score',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
    ]
