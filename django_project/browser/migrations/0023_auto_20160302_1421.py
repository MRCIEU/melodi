# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0022_auto_20160208_1506'),
    ]

    operations = [
        migrations.CreateModel(
            name='Compare',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_id', models.CharField(max_length=200)),
                ('job_name', models.CharField(max_length=200)),
                ('job_desc', models.CharField(max_length=400)),
                ('job_id', models.CharField(max_length=200)),
                ('job_start', models.CharField(max_length=30)),
                ('job_status', models.CharField(max_length=20)),
                ('job_progress', models.IntegerField()),
                ('job_type', models.CharField(max_length=20)),
            ],
        ),
        migrations.AlterField(
            model_name='overlap',
            name='mc_id',
            field=models.ForeignKey(to='browser.Compare'),
        ),
        migrations.DeleteModel(
            name='MeshCompare',
        ),
    ]
