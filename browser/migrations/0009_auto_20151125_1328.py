# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0008_meshcompare_meshmain'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchset',
            name='meshMain',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='searchset',
            name='meshNotMain',
            field=models.BooleanField(default=False),
        ),
    ]
