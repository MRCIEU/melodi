# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0011_auto_20151125_1402'),
    ]

    operations = [
        migrations.RenameField(
            model_name='searchsetanalysis',
            old_name='meshMainFET',
            new_name='complete',
        ),
        migrations.RemoveField(
            model_name='searchsetanalysis',
            name='meshNotMainFET',
        ),
        migrations.AddField(
            model_name='searchsetanalysis',
            name='type',
            field=models.CharField(default=False, max_length=20),
            preserve_default=False,
        ),
    ]
