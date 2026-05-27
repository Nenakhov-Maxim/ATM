from django.core.management.base import BaseCommand
from worker.models import Users_analytics
from master.models import WorkerAnalyticsRecord, Tasks
from django.db import transaction

class Command(BaseCommand):
    help = 'Migrate Users_analytics HStore data to WorkerAnalyticsRecord normalized table'

    def handle(self, *args, **options):
        migrated = 0
        with transaction.atomic():
            for ua in Users_analytics.objects.all():
                user = ua.userId
                # profile_amount: dict like {'5.2026': '12:10;13:5;'}
                for month_key, val_str in (ua.profile_amount or {}).items():
                    try:
                        month_s, year_s = month_key.split('.')
                        month = int(month_s)
                        year = int(year_s)
                    except Exception:
                        continue
                    # parse settingUp and work_time if present
                    setting_map = (ua.settingUp or {}).get(month_key, '')
                    work_map = (ua.work_time or {}).get(month_key, '')
                    # build dicts task_id -> values
                    profile_pairs = [p for p in val_str.split(';') if p]
                    setting_pairs = [p for p in setting_map.split(';') if p]
                    work_pairs = [p for p in work_map.split(';') if p]
                    profile_dict = {}
                    for p in profile_pairs:
                        try:
                            t_id, v = p.split(':')
                            profile_dict[int(t_id)] = int(v)
                        except Exception:
                            continue
                    setting_dict = {}
                    for p in setting_pairs:
                        try:
                            t_id, v = p.split(':')
                            setting_dict[int(t_id)] = float(v)
                        except Exception:
                            continue
                    work_dict = {}
                    for p in work_pairs:
                        try:
                            t_id, v = p.split(':')
                            work_dict[int(t_id)] = float(v)
                        except Exception:
                            continue
                    # for each task id in profile_dict create WorkerAnalyticsRecord
                    for task_id, profile_amount in profile_dict.items():
                        if not Tasks.objects.filter(id=task_id).exists():
                            continue
                        setting_up = setting_dict.get(task_id, 0.0)
                        work_time = work_dict.get(task_id, 0.0)
                        try:
                            WorkerAnalyticsRecord.objects.update_or_create(
                                user=user,
                                task_id=task_id,
                                month=month,
                                year=year,
                                defaults={
                                    'setting_up_hours': setting_up,
                                    'profile_amount': profile_amount,
                                    'work_time_hours': work_time,
                                }
                            )
                            migrated += 1
                        except Exception:
                            continue
        self.stdout.write(self.style.SUCCESS(f'Migrated {migrated} analytics records'))
