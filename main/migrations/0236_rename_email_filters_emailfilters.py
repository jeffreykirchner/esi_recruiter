# Generated by Django 4.2.13 on 2024-06-06 23:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0235_rename_account_types_accounttypes'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='email_filters',
            new_name='EmailFilters',
        ),
    ]