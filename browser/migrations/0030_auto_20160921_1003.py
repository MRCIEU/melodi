# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0029_auto_20160628_1223'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fet',
            name='ssa_id',
        ),
        migrations.AlterField(
            model_name='overlap',
            name='name',
            field=models.CharField(unique=True, max_length=250),
        ),
        migrations.DeleteModel(
            name='Fet',
        ),
    ]
