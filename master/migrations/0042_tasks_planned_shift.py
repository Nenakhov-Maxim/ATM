from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('master', '0041_tasks_task_order_number')]

    operations = [
        migrations.AddField(
            model_name='tasks', name='task_shift_date',
            field=models.DateField(blank=True, null=True, verbose_name='Дата производственных суток'),
        ),
        migrations.AddField(
            model_name='tasks', name='task_shift',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True, verbose_name='Плановая смена',
                choices=[(1, '1 смена (08:00 - 17:00)'), (2, '2 смена (17:00 - 01:00)'), (3, '3 смена (01:00 - 08:00)')],
            ),
        ),
    ]
