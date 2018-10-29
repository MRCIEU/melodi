# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0013_meshcompare_job_desc'),
    ]

    operations = [
        migrations.RenameField(
            model_name='searchsetanalysis',
            old_name='type',
            new_name='job_type',
        ),
        migrations.AddField(
            model_name='meshcompare',
            name='job_type',
            field=models.CharField(default='meshMain', max_length=20),
            preserve_default=False,
        ),
    ]
