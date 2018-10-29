# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0026_auto_20160427_1003'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchsetanalysis',
            name='year_range',
            field=models.CharField(default='', max_length=10),
            preserve_default=False,
        ),
    ]
