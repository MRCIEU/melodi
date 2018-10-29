# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0025_auto_20160427_1001'),
    ]

    operations = [
        migrations.RenameField(
            model_name='compare',
            old_name='yearRange',
            new_name='year_range',
        ),
    ]
