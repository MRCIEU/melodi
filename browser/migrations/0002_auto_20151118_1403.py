# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobs',
            name='job_start',
            field=models.CharField(default=datetime.datetime(2015, 11, 18, 14, 3, 8, 918806, tzinfo=utc), max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='jobs',
            name='job_type',
            field=models.CharField(default='search_set', max_length=200),
            preserve_default=False,
        ),
    ]
