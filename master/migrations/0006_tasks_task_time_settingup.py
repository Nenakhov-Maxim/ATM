# Generated by Django 4.2.15 on 2024-09-19 11:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0005_tasks_task_is_vision'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasks',
            name='task_time_settingUp',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Фактическая дата и время начала наладки'),
        ),
    ]
