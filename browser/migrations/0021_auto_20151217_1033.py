# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0020_overlap_score'),
    ]

    operations = [
        migrations.AlterField(
            model_name='searchset',
            name='ss_file',
            field=models.FileField(upload_to=b'/var/django/temmpo2/abstracts'),
        ),
    ]
