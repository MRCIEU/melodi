# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0021_auto_20151217_1033'),
    ]

    operations = [
        migrations.AddField(
            model_name='overlap',
            name='treeLevel',
            field=models.FloatField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='searchset',
            name='ss_file',
            field=models.FileField(upload_to=b'/var/django/melodi/abstracts'),
        ),
    ]
