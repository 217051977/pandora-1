# Generated by Django 2.2.6 on 2019-12-01 17:44

import contest.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contest', '0004_contest_in_files'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contest',
            name='in_files',
            field=models.FileField(blank=True, null=True, upload_to=contest.models.get_contest_ins_files_path),
        ),
    ]
