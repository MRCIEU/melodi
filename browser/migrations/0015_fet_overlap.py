# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0014_auto_20151126_0940'),
    ]

    operations = [
        migrations.CreateModel(
            name='Fet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('odds', models.FloatField()),
                ('pval', models.FloatField()),
                ('cpval', models.FloatField()),
                ('ssa_id', models.ForeignKey(to='browser.SearchSetAnalysis')),
            ],
        ),
        migrations.CreateModel(
            name='Overlap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mean_cp', models.FloatField()),
                ('mean_odds', models.FloatField()),
                ('uniq_a', models.IntegerField()),
                ('uniq_b', models.FloatField()),
                ('shared', models.FloatField()),
                ('mc_id', models.ForeignKey(to='browser.MeshCompare')),
            ],
        ),
    ]
