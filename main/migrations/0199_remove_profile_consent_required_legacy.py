# Generated by Django 4.0.7 on 2022-09-02 16:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0198_alter_consentform_pdf_file'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='consent_required_legacy',
        ),
    ]