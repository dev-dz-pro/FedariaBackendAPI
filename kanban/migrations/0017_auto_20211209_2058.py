# Generated by Django 3.2.7 on 2021-12-09 19:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kanban', '0016_userdirectmessages'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userdirectmessages',
            old_name='from_usr',
            new_name='receiver_user',
        ),
        migrations.RenameField(
            model_name='userdirectmessages',
            old_name='iuser',
            new_name='sender_user',
        ),
    ]
