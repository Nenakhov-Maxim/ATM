from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('login', '0010_workplace_production_area_id')]
    operations = [
        migrations.AddField(
            model_name='user', name='available_areas',
            field=models.ManyToManyField(
                to='login.productionarea', blank=True, related_name='managers',
                verbose_name='Доступные участки',
                help_text='Участки для управления задачами. Основной участок также всегда доступен.',
            ),
        ),
    ]
