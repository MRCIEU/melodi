# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0027_searchsetanalysis_year_range'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='compare',
            name='job_id',
        ),
    ]
