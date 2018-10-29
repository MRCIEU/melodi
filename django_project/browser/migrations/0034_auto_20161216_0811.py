# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0033_auto_20161105_1835'),
    ]

    operations = [
        #migrations.AddField(
        #    model_name='compare',
        #    name='share',
        #    field=models.BooleanField(default=False),
        #),
        migrations.AlterField(
            model_name='compare',
            name='user_id',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='overlap',
            name='name',
            field=models.CharField(max_length=500),
        ),
    ]
