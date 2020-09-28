# Generated by Django 3.0.7 on 2020-09-03 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0073_profile_paused'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiments',
            name='experiment_manager',
            field=models.CharField(default='***Manager Here***', max_length=300),
        ),
        migrations.AlterField(
            model_name='experiments',
            name='length_default',
            field=models.IntegerField(default=60),
        ),
        migrations.AlterField(
            model_name='experiments',
            name='title',
            field=models.CharField(default='***New Experiment***', max_length=300),
        ),
    ]