# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0028_remove_compare_job_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='compare',
            name='year_range',
            field=models.CharField(max_length=12),
        ),
        migrations.AlterField(
            model_name='searchsetanalysis',
            name='year_range',
            field=models.CharField(max_length=12),
        ),
    ]
