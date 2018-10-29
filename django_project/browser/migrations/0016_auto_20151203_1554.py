# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0015_fet_overlap'),
    ]

    operations = [
        migrations.AlterField(
            model_name='overlap',
            name='shared',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='overlap',
            name='uniq_b',
            field=models.IntegerField(),
        ),
    ]
