# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0023_auto_20160302_1421'),
    ]

    operations = [
        migrations.AddField(
            model_name='compare',
            name='add_info',
            field=models.CharField(default='', max_length=500),
            preserve_default=False,
        ),
    ]
