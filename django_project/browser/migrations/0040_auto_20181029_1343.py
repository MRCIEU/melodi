# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0039_auto_20170222_2153'),
    ]

    operations = [
        migrations.AddField(
            model_name='compare',
            name='share',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='compare',
            name='hash_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, db_index=True),
        ),
    ]
