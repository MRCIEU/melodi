# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0002_auto_20151118_1403'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobs',
            name='job_name',
            field=models.CharField(default='test', max_length=200),
            preserve_default=False,
        ),
    ]
