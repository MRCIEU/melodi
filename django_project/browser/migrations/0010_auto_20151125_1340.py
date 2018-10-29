# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0009_auto_20151125_1328'),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchSetAnalysis',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('meshMainFET', models.BooleanField(default=False)),
                ('meshNotMainFET', models.BooleanField(default=False)),
            ],
        ),
        migrations.RemoveField(
            model_name='meshcompare',
            name='meshMain',
        ),
        migrations.RemoveField(
            model_name='searchset',
            name='meshMain',
        ),
        migrations.RemoveField(
            model_name='searchset',
            name='meshNotMain',
        ),
        migrations.AddField(
            model_name='searchsetanalysis',
            name='ss_id',
            field=models.ForeignKey(to='browser.SearchSet'),
        ),
    ]
