# Generated by Django 5.1 on 2024-08-15 06:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0001_initial'),
        ('master', '0004_mastertypeproblem'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='production_area_id',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='master.workplace'),
        ),
    ]
