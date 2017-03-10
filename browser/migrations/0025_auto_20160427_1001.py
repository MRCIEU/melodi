# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0024_compare_add_info'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='compare',
            name='add_info',
        ),
        migrations.AddField(
            model_name='compare',
            name='yearRange',
            field=models.CharField(default='', max_length=10),
            preserve_default=False,
        ),
    ]
