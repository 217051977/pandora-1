# Generated by Django 2.2.6 on 2019-12-01 18:09

import contest.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contest', '0005_auto_20191201_1744'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='out_files',
            field=models.FileField(blank=True, null=True, upload_to=contest.models.get_contest_outs_files_path),
        ),
    ]
