# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('browser', '0004_jobs_params'),
    ]

    operations = [
        migrations.CreateModel(
            name='MeshCompare',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_id', models.CharField(max_length=200)),
                ('job_name', models.CharField(max_length=200)),
                ('job_id', models.CharField(max_length=200)),
                ('job_start', models.CharField(max_length=30)),
                ('job_status', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='SearchSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_id', models.CharField(max_length=200)),
                ('ss_name', models.CharField(max_length=200)),
                ('job_id', models.CharField(max_length=200)),
                ('job_start', models.CharField(max_length=30)),
                ('job_status', models.CharField(max_length=20)),
                ('file', models.CharField(max_length=200)),
                ('ss_desc', models.CharField(max_length=500)),
            ],
        ),
        migrations.DeleteModel(
            name='Jobs',
        ),
        migrations.AlterUniqueTogether(
            name='searchset',
            unique_together=set([('user_id', 'ss_name')]),
        ),
    ]
