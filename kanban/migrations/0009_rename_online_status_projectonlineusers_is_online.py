# Generated by Django 3.2.7 on 2021-11-28 12:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kanban', '0008_projectonlineusers'),
    ]

    operations = [
        migrations.RenameField(
            model_name='projectonlineusers',
            old_name='online_status',
            new_name='is_online',
        ),
    ]