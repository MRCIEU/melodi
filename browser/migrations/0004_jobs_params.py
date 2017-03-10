# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0003_jobs_job_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobs',
            name='params',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
