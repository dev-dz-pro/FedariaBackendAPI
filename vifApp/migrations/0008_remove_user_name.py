# Generated by Django 3.2.7 on 2021-10-16 13:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vifApp', '0007_user_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='name',
        ),
    ]
