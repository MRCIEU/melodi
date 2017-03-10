# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0012_auto_20151125_1436'),
    ]

    operations = [
        migrations.AddField(
            model_name='meshcompare',
            name='job_desc',
            field=models.CharField(default='no desc', max_length=400),
            preserve_default=False,
        ),
    ]
