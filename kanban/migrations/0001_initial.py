# Generated by Django 3.2.7 on 2021-10-12 10:32

from django.db import migrations, models
import django.db.models.deletion
import kanban.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Portfolio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('portfolio_name', models.CharField(max_length=50)),
                ('pined_portfolio', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('project_description', models.CharField(max_length=250)),
                ('pined_project', models.BooleanField(default=False)),
                ('agile_framwork', models.CharField(choices=[('Scrum', 'Scrum'), ('Kanban', 'Kanban')], default='Kanban', max_length=6)),
                ('product_owner', models.EmailField(max_length=254)),
                ('scrum_master', models.EmailField(max_length=254)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('board', models.JSONField(default=kanban.models.board_default)),
                ('portfolio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='kanban.portfolio')),
            ],
        ),
    ]
