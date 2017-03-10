# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0037_auto_20170222_1847'),
    ]

    operations = [
        #migrations.AddField(
        #    model_name='compare',
        #    name='share',
        #    field=models.BooleanField(default=False),
        #),
        migrations.AlterField(
            model_name='overlap',
            name='name',
            field=models.CharField(db_index=True, max_length=500, blank=True),
        ),
        migrations.AlterField(
            model_name='overlap',
            name='name1',
            field=models.CharField(db_index=True, max_length=200, blank=True),
        ),
        migrations.AlterField(
            model_name='overlap',
            name='name2',
            field=models.CharField(db_index=True, max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='overlap',
            name='name3',
            field=models.CharField(db_index=True, max_length=200, blank=True),
        ),
        migrations.AlterField(
            model_name='overlap',
            name='name4',
            field=models.CharField(db_index=True, max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='overlap',
            name='name5',
            field=models.CharField(db_index=True, max_length=200, blank=True),
        ),
    ]
