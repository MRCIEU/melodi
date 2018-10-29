# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0016_auto_20151203_1554'),
    ]

    operations = [
        migrations.AddField(
            model_name='overlap',
            name='name',
            field=models.CharField(default='', max_length=500),
            preserve_default=False,
        ),
    ]
