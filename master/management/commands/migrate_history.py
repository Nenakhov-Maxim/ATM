from django.core.management.base import BaseCommand
from master.models import Tasks, HistoryEvent, HistoryProfileRecords, TaskEvent, TaskProfileRecord
from django.db import transaction

class Command(BaseCommand):
    help = 'Migrate legacy history_event_messages and history_profile_records (M2M) to normalized TaskEvent and TaskProfileRecord'

    def handle(self, *args, **options):
        total_events = 0
        total_profiles = 0
        with transaction.atomic():
            for task in Tasks.objects.all():
                # migrate history events
                for he in task.history_event_messages.all():
                    obj, created = TaskEvent.objects.get_or_create(
                        task=task,
                        user=he.user,
                        type_event=he.type_event,
                        message=he.message,
                        created_at=he.created_at,
                    )
                    if created:
                        total_events += 1
                # migrate profile records
                for hr in task.history_profile_records.all():
                    obj, created = TaskProfileRecord.objects.get_or_create(
                        task=task,
                        user=hr.user,
                        amount=hr.amount,
                        profile_sum=hr.profile_sum,
                        created_at=hr.created_at,
                    )
                    if created:
                        total_profiles += 1
        self.stdout.write(self.style.SUCCESS(f'Migrated {total_events} events and {total_profiles} profile records'))
