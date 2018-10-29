# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0038_auto_20170222_1851'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sliders',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('version', models.IntegerField()),
                ('type', models.CharField(max_length=20)),
                ('pval', models.FloatField(blank=True)),
                ('odds', models.FloatField(blank=True)),
                ('level', models.IntegerField(blank=True)),
                ('top', models.IntegerField(blank=True)),
            ],
        ),
        #migrations.AddField(
        #    model_name='compare',
        #    name='share',
        #    field=models.BooleanField(default=False),
        #),
        migrations.AddField(
            model_name='sliders',
            name='com',
            field=models.ForeignKey(to='browser.Compare'),
        ),
    ]
