# Generated by Django 3.2.7 on 2021-09-19 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vifApp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='github_id',
            field=models.BigIntegerField(blank=True, null=True, unique=True),
        ),
    ]
