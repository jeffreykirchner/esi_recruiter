# Generated by Django 3.1.2 on 2020-10-02 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0106_faq'),
    ]

    operations = [
        migrations.AlterField(
            model_name='faq',
            name='answer',
            field=models.CharField(max_length=10000),
        ),
    ]