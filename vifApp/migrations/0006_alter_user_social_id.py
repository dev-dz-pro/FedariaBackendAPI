# Generated by Django 3.2.7 on 2021-10-15 13:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vifApp', '0005_alter_user_social_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='social_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
