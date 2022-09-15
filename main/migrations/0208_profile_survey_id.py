# Generated by Django 4.0.7 on 2022-09-15 19:43

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0207_alter_profileconsentform_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='survey_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
    ]