# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0005_auto_20151125_1110'),
    ]

    operations = [
        migrations.RenameField(
            model_name='searchset',
            old_name='file',
            new_name='ss_file',
        ),
    ]
