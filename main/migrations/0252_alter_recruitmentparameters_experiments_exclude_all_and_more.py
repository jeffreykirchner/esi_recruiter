# Generated by Django 4.2.13 on 2024-06-24 22:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0251_rename_subject_types_subjecttypes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recruitmentparameters',
            name='experiments_exclude_all',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='recruitmentparameters',
            name='institutions_exclude_all',
            field=models.BooleanField(default=False),
        ),
    ]
