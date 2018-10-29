# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0007_auto_20151125_1251'),
    ]

    operations = [
        migrations.AddField(
            model_name='meshcompare',
            name='meshMain',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]
