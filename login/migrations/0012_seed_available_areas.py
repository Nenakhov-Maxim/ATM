from django.db import migrations


def seed_areas(apps, schema_editor):
    User = apps.get_model('login', 'User')
    links = User.available_areas.through
    alias = schema_editor.connection.alias
    for user in User.objects.using(alias).exclude(production_area_id__isnull=True).iterator():
        links.objects.using(alias).get_or_create(user_id=user.pk, productionarea_id=user.production_area_id_id)


class Migration(migrations.Migration):
    dependencies = [('login', '0011_user_available_areas')]
    operations = [migrations.RunPython(seed_areas, migrations.RunPython.noop)]
