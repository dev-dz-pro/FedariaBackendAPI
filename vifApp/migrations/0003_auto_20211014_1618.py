# Generated by Django 3.2.7 on 2021-10-14 15:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vifApp', '0002_alter_user_profile_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='github_id',
        ),
        migrations.AddField(
            model_name='user',
            name='social_id',
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
