# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0006_auto_20151125_1113'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchset',
            name='pTotal',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='searchset',
            name='ss_file',
            field=models.FileField(upload_to=b''),
        ),
    ]
