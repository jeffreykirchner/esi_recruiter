# Generated by Django 4.2.11 on 2024-04-09 23:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0232_alter_consentform_pdf_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiments',
            name='notes',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='experiments',
            name='special_instructions_default',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
    ]