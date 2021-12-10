# Generated by Django 3.2.7 on 2021-12-06 20:00

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kanban', '0012_alter_projectgroupechat_prj'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectgroupechat',
            name='attachments',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.URLField(max_length=600), blank=True, null=True, size=None),
        ),
    ]