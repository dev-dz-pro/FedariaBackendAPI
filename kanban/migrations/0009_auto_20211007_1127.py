# Generated by Django 3.2.7 on 2021-10-07 10:27

from django.db import migrations, models
import django.db.models.deletion
import kanban.models


class Migration(migrations.Migration):

    dependencies = [
        ('kanban', '0008_kanbanboard_project_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('project_description', models.CharField(max_length=250)),
                ('agile_framwork', models.CharField(choices=[('Scrum', 'Scrum'), ('Kanban', 'Kanban')], default='Kanban', max_length=6)),
                ('product_owner', models.EmailField(max_length=254)),
                ('scrum_master', models.EmailField(max_length=254)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('board', models.JSONField(default=kanban.models.board_default)),
                ('portfolio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='kanban.portfolio')),
            ],
            options={
                'unique_together': {('name', 'portfolio')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='kanbanboard',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='kanbanboard',
            name='portfolio',
        ),
        migrations.AlterUniqueTogether(
            name='task',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='task',
            name='col',
        ),
        migrations.DeleteModel(
            name='BoardCol',
        ),
        migrations.DeleteModel(
            name='KanbanBoard',
        ),
        migrations.DeleteModel(
            name='Task',
        ),
    ]
