# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0032_auto_20161104_0844'),
    ]

    operations = [
        migrations.AddField(
            model_name='compare',
            name='hash_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        #migrations.AddField(
        #    model_name='compare',
        #    name='share',
        #    field=models.BooleanField(default=False),
        #),
        migrations.AlterField(
            model_name='compare',
            name='user_id',
            field=models.CharField(unique=True, max_length=200),
        ),
    ]
