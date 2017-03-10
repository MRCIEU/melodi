# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0017_overlap_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchset',
            name='job_progress',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
