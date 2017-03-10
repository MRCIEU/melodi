# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0035_auto_20170107_0636'),
    ]

    operations = [
        migrations.CreateModel(
            name='Filters',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('version', models.IntegerField()),
                ('type', models.CharField(max_length=20)),
                ('num', models.IntegerField()),
                ('value', models.CharField(max_length=200)),
                ('location', models.IntegerField()),
                ('ftype', models.CharField(max_length=3)),
            ],
        ),
        #migrations.AddField(
        #    model_name='compare',
        #    name='share',
        #    field=models.BooleanField(default=False),
        #),
        migrations.AddField(
            model_name='filters',
            name='com',
            field=models.ForeignKey(to='browser.Compare'),
        ),
    ]
