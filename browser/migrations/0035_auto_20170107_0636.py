# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0034_auto_20161216_0811'),
    ]

    operations = [
        #migrations.AddField(
        #    model_name='compare',
        #    name='share',
        #    field=models.BooleanField(default=False),
        #),
        migrations.AlterField(
            model_name='searchset',
            name='ss_desc',
            field=models.CharField(max_length=5000),
        ),
    ]
