import json
from datetime import date, datetime, timedelta, timezone

from django.test import RequestFactory, SimpleTestCase, TestCase

from login.models import ProductionArea, User, Workplace
from .forms import TaskScheduleForm
from .models import CoatingType, ProfileType, Tasks, TaskStatus, TypeEvent, WorkerAnalyticsRecord
from .profiling_invoice_report import _build_report_rows, _get_completed_tasks, SHIFT_1, SHIFT_2
from .shifts import PRODUCTION_TIME_ZONE, production_shift_at, shift_bounds
from .views import edit_task, new_task


class ShiftScheduleTests(SimpleTestCase):
    def test_all_shifts_and_midnight_belong_to_same_production_day(self):
        day = date(2026, 9, 10)
        expected = {
            1: (datetime(2026, 9, 10, 3, tzinfo=timezone.utc), 9),
            2: (datetime(2026, 9, 10, 12, tzinfo=timezone.utc), 8),
            3: (datetime(2026, 9, 10, 20, tzinfo=timezone.utc), 7),
        }
        for shift, (start, hours) in expected.items():
            with self.subTest(shift=shift):
                form = TaskScheduleForm({'task_shift_date': '2026-09-10', 'task_shift': str(shift)})
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.cleaned_data['task_timedate_start'], start)
                self.assertEqual(form.cleaned_data['task_timedate_end'], start + timedelta(hours=hours))
                self.assertEqual(production_shift_at(start), (day, shift))
                self.assertEqual(production_shift_at(start + timedelta(hours=hours) - timedelta(seconds=1)), (day, shift))
        self.assertEqual(production_shift_at(shift_bounds(day, 3)[1]), (day + timedelta(days=1), 1))

    def test_invalid_and_missing_shift_are_rejected(self):
        for shift in ('', '0', '4', 'invalid'):
            with self.subTest(shift=shift):
                self.assertFalse(TaskScheduleForm({'task_shift_date': '2026-09-10', 'task_shift': shift}).is_valid())
        self.assertFalse(TaskScheduleForm({'task_shift': '1'}).is_valid())


class TaskShiftWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.area = ProductionArea.objects.create(production_area_name='Test area')
        cls.master = User.objects.create(username='master', is_superuser=True, production_area_id=cls.area)
        cls.workers = [User.objects.create(username=f'worker-{i}') for i in range(2)]
        cls.line = Workplace.objects.create(workplace_name='Line', type_of_equipment='Line', inv_number=1, production_area_id=cls.area)
        cls.profile = ProfileType.objects.create(profile_name='Profile')
        cls.coating = CoatingType.objects.create(name='Paint')
        for pk in (1, 2, 3):
            TaskStatus.objects.create(pk=pk, status_name=f'Status {pk}')
        for pk in (1, 9):
            TypeEvent.objects.create(pk=pk, type_name=f'Event {pk}', color='#000000')

    def payload(self, **changes):
        data = {
            'task_name': 'Profile task', 'task_shift_date': '2026-09-10', 'task_shift': '1',
            'task_profile_type': self.profile.pk, 'task_workplace': self.line.pk,
            'task_profile_length': '3', 'task_profile_amount': '100', 'task_order_number': 'Order-1',
            'task_coating_type': '', 'task_coating_thickness': '', 'task_comments': 'Test',
        }
        data.update(changes)
        return data

    def request(self, method, data):
        request = getattr(RequestFactory(), method)('/master/task/', data=data)
        request.user = self.master
        return request

    def create_task(self):
        response = new_task(self.request('post', self.payload()))
        self.assertEqual(response.status_code, 301, response.content)
        return Tasks.objects.latest('id')

    def test_lengths_keep_orders_and_coverings_but_share_entire_shift(self):
        response = new_task(self.request('post', self.payload(
            task_shift='2', task_profile_length=['2', '4'], task_profile_amount=['10', '20'],
            task_order_number=['Order-A', 'Order-B'], task_coating_type=['', str(self.coating.pk)],
        )))
        self.assertEqual(response.status_code, 301, response.content)
        tasks = list(Tasks.objects.order_by('id'))
        self.assertEqual(len(tasks), 2)
        for task in tasks:
            self.assertEqual(task.task_shift_date, date(2026, 9, 10))
            self.assertEqual(task.task_shift, 2)
            self.assertEqual((task.task_timedate_start, task.task_timedate_end), shift_bounds(date(2026, 9, 10), 2))
            self.assertIn(task.planned_shift_label, task.history_event_messages.get().message)
            self.assertIn(task.planned_shift_label, task.events.get().message)
        self.assertEqual([t.task_order_number for t in tasks], ['Order-A', 'Order-B'])
        self.assertEqual([t.task_coating_type_id for t in tasks], [None, self.coating.pk])

    def test_invalid_second_length_does_not_create_first_task(self):
        response = new_task(self.request('post', self.payload(
            task_profile_length=['3', 'bad'], task_profile_amount=['10', '20'],
            task_order_number=['A', 'B'], task_coating_type=['', ''],
        )))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Tasks.objects.exists())

    def test_replanning_preserves_workers_actual_output_and_report_shifts(self):
        task = self.create_task()
        other = self.create_task()
        actual_start = datetime(2026, 9, 10, 8, tzinfo=PRODUCTION_TIME_ZONE)
        actual_end = datetime(2026, 9, 10, 18, tzinfo=PRODUCTION_TIME_ZONE)
        task.task_timedate_start_fact = actual_start
        task.task_timedate_end_fact = actual_end
        task.task_status_id = 2
        task.profile_amount_now = 30
        task.save()
        for user, amount, hour in zip(self.workers, (10, 20), (9, 17)):
            timestamp = datetime(2026, 9, 10, hour, tzinfo=PRODUCTION_TIME_ZONE)
            task.history_profile_records.create(user=user, amount=amount, created_at=timestamp)
            task.profile_records.create(user=user, amount=amount, created_at=timestamp)
            WorkerAnalyticsRecord.objects.create(user=user, task=task, month=9, year=2026, profile_amount=amount)
        before = list(task.history_profile_records.values('id', 'user_id', 'amount', 'created_at'))
        normalized_before = list(task.profile_records.values('id', 'user_id', 'amount', 'created_at'))

        # Opening another task must not redirect this edit to a shared global ID.
        edit_task(self.request('get', {'id_task': other.pk}))
        response = edit_task(self.request('post', self.payload(id_task=task.pk, task_shift='3')))
        self.assertEqual(response.status_code, 301, response.content)
        task.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual((task.task_shift, other.task_shift), (3, 1))
        self.assertEqual(task.task_timedate_start_fact, actual_start)
        self.assertEqual(task.task_timedate_end_fact, actual_end)
        self.assertEqual(task.profile_amount_now, 30)
        self.assertEqual(list(task.history_profile_records.values('id', 'user_id', 'amount', 'created_at')), before)
        self.assertEqual(list(task.profile_records.values('id', 'user_id', 'amount', 'created_at')), normalized_before)
        self.assertEqual(list(WorkerAnalyticsRecord.objects.filter(task=task).order_by('user_id').values_list('profile_amount', flat=True)), [10, 20])
        self.assertIn('3 смена', task.events.get(type_event_id=9).message)

        start = datetime(2026, 9, 10, 8, tzinfo=PRODUCTION_TIME_ZONE)
        rows = _build_report_rows(_get_completed_tasks(start, start + timedelta(days=1), self.master))
        self.assertEqual(len(rows), 1)
        self.assertEqual(dict(rows[0]['profile_by_shift']), {SHIFT_1: 10, SHIFT_2: 20})

    def test_legacy_night_task_suggests_previous_production_date_without_modifying_it(self):
        start = datetime(2026, 9, 11, 2, tzinfo=PRODUCTION_TIME_ZONE)
        task = Tasks.objects.create(task_name='Legacy', task_profile_amount=10, task_timedate_start=start)
        response = edit_task(self.request('get', {'id_task': task.pk}))
        data = json.loads(response.content)
        self.assertEqual((data['task_shift_date'], data['task_shift']), ('2026-09-10', 3))
        task.refresh_from_db()
        self.assertIsNone(task.task_shift)
        self.assertEqual(task.task_timedate_start, start)
