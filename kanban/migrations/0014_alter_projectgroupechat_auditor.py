# Generated by Django 3.2.7 on 2021-12-06 21:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('kanban', '0013_alter_projectgroupechat_attachments'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectgroupechat',
            name='auditor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
