# Generated by Django 4.0.6 on 2022-07-15 21:00

from django.db import migrations
import django.db.models.functions.text


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0186_alter_profile_trait_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='traits',
            options={'ordering': [django.db.models.functions.text.Lower('name')], 'verbose_name': 'Trait', 'verbose_name_plural': 'Traits'},
        ),
    ]