# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0030_auto_20160921_1003'),
    ]

    operations = [
        migrations.AlterField(
            model_name='overlap',
            name='name',
            field=models.CharField(max_length=250),
        ),
        migrations.AlterUniqueTogether(
            name='overlap',
            unique_together=set([('name', 'mc_id')]),
        ),
    ]
