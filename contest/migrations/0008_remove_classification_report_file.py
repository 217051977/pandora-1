# Generated by Django 2.2.6 on 2020-03-04 15:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contest', '0007_auto_20200109_1152'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='classification',
            name='report_file',
        ),
    ]
