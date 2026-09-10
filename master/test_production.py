import json
from datetime import date, timedelta
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.utils import timezone
from openpyxl import load_workbook

from login.models import ProductionArea, User, Workplace
from app.views import arduino_data
from worker.production_views import update_coating, complete_production, stock_decision
from .databaseWork import DatabaseWork
from .models import Tasks, TaskStatus, TypeEvent, ProfileType, CoatingType, ShtripsValueType, WorkerAnalyticsRecord
from .production import change_coating, finish_task, decide_stock, record_total, ProductionConflict
from .profiling_invoice_report import _get_completed_tasks, _build_report_rows, _write_workbook, SHIFT_1, SHIFT_2
from .shifts import shift_bounds


class ProductionWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.area = ProductionArea.objects.create(production_area_name='Test')
        cls.line = Workplace.objects.create(pk=1, workplace_name='Line', type_of_equipment='Line', inv_number=1, production_area_id=cls.area)
        cls.user = User.objects.create(username='first', is_superuser=True, production_area_id=cls.area)
        cls.second = User.objects.create(username='second', is_superuser=True, production_area_id=cls.area)
        cls.profile = ProfileType.objects.create(profile_name='PK 60/40', association_name_shtrips='240')
        cls.paint = CoatingType.objects.create(name='Paint')
        cls.kg = ShtripsValueType.objects.create(type_offs_shtrips='kg')
        for pk in (1, 2, 3, 7, 8):
            TaskStatus.objects.create(pk=pk, status_name=f'Status {pk}')
        for pk in (1, 3, 6, 8, 9):
            TypeEvent.objects.create(pk=pk, type_name=f'Event {pk}', color='#000000')

    def task(self, **changes):
        data = dict(
            task_name='Order', task_workplace=self.line, task_profile_type=self.profile,
            task_profile_amount=200, task_profile_length=3, task_order_number='Order-123',
            task_profile_material=1.2, task_coating_thickness='z275', task_coating_type=self.paint,
            task_status_id=3, task_timedate_start_fact=timezone.now() - timedelta(hours=1), allow_stock=True,
        )
        data.update(changes)
        task = Tasks.objects.create(**data)
        task.events.create(user=self.user, type_event_id=3, message='Start')
        return task

    def request(self, data, user=None):
        request = RequestFactory().post('/worker/', data=json.dumps(data), content_type='application/json', REMOTE_ADDR='192.168.211.10')
        request.user = user or self.user
        return request

    def test_split_output_preserves_users_and_excel_weights(self):
        task = self.task()
        record_total(task, 100, self.user)
        task.history_offs_shtrips.create(value=500, type_value_id=self.kg, coating_thickness='z275')
        task = change_coating(task.pk, self.line.pk, self.user, 'z140', 120, 100, 0)
        record_total(task, 200, self.second)
        task.history_offs_shtrips.create(value=600, type_value_id=self.kg, coating_thickness='z140')
        task = finish_task(task.pk, self.line.pk, self.second, 200, 200, 1)
        rows = list(task.history_profile_records.order_by('id').values_list('amount', 'user_id', 'coating_thickness'))
        self.assertEqual(rows, [(100, self.user.pk, 'z275'), (20, self.user.pk, 'z275'), (80, self.second.pk, 'z140')])
        self.assertEqual(list(task.profile_records.order_by('id').values_list('amount', 'user_id', 'coating_thickness')), rows)
        start, end = timezone.now() - timedelta(days=1), timezone.now() + timedelta(days=1)
        groups = _build_report_rows(_get_completed_tasks(start, end, self.user))
        self.assertEqual(len(groups), 2)
        self.assertEqual([sum(g['profile_by_shift'].values()) for g in groups], [120, 80])
        self.assertEqual([sum(g['shtrips_by_shift'].values()) for g in groups], [500, 600])
        with TemporaryDirectory() as folder:
            path = str(Path(folder) / 'invoice.xlsx')
            _write_workbook(path, groups, start, end)
            book = load_workbook(path)
            sheet = book.active
            self.assertIn('z275', sheet['B4'].value)
            self.assertIn('z140', sheet['B6'].value)
            self.assertEqual((sheet['L4'].value, sheet['L6'].value), (120, 80))
            self.assertEqual(sheet['X8'].value, 1100)
            book.close()

    def test_legacy_records_are_frozen_before_first_change(self):
        task = self.task(profile_amount_now=30)
        task.history_profile_records.create(user=self.user, amount=30, profile_sum=30)
        task.profile_records.create(user=self.user, amount=30, profile_sum=30)
        task.history_offs_shtrips.create(value=500, type_value_id=self.kg)
        change_coating(task.pk, self.line.pk, self.user, 'z140', 30, 30, 0)
        for relation in (task.history_profile_records, task.profile_records, task.history_offs_shtrips):
            self.assertEqual(relation.get().coating_thickness, 'z275')

    def test_coating_quantities_follow_actual_not_planned_shift(self):
        day = date(2026, 9, 10)
        start, boundary = shift_bounds(day, 1)
        task = self.task(task_shift_date=day, task_shift=3)
        with patch('master.production.timezone.now', return_value=start + timedelta(hours=1)):
            task = change_coating(task.pk, self.line.pk, self.user, 'z140', 120, 0, 0)
        with patch('master.production.timezone.now', return_value=boundary + timedelta(hours=1)):
            finish_task(task.pk, self.line.pk, self.second, 200, 120, 1)
        groups = _build_report_rows(_get_completed_tasks(start, start + timedelta(days=1), self.user))
        self.assertEqual(dict(groups[0]['profile_by_shift']), {SHIFT_1: 120})
        self.assertEqual(dict(groups[1]['profile_by_shift']), {SHIFT_2: 80})

    def test_failed_master_edit_rolls_back_coating_and_history(self):
        task = self.task()
        task.history_profile_records.create(user=self.user, amount=0, profile_sum=0)
        data = {'task_coating_thickness': 'z140', 'task_shift_date': date(2026, 9, 10), 'task_shift': 1}
        result = DatabaseWork(data).edit_data_from_task(task.pk, self.user)
        self.assertIsInstance(result, str)
        task.refresh_from_db()
        self.assertEqual((task.task_coating_thickness, task.coating_revision), ('z275', 0))
        self.assertIsNone(task.history_profile_records.get().coating_thickness)
        self.assertFalse(task.events.filter(type_event_id=9).exists())
        self.assertFalse(task.history_event_messages.filter(type_event_id=9).exists())

    def test_stale_counter_and_delayed_manual_request_are_rejected(self):
        task = self.task()
        record_total(task, 10, self.user)
        with self.assertRaises(ProductionConflict):
            change_coating(task.pk, self.line.pk, self.user, 'z140', 10, 9, 0)
        change_coating(task.pk, self.line.pk, self.user, 'z140', 10, 10, 0)
        self.assertFalse(DatabaseWork({}).change_profile_amount(task.pk, 20, self.user, revision=0))
        with self.assertRaises(ValueError):
            change_coating(task.pk, self.line.pk, self.user, 'z275', 9, 10, 1)
        task.refresh_from_db()
        self.assertEqual((task.profile_amount_now, task.task_coating_thickness), (10, 'z140'))

    def test_return_to_same_coating_still_changes_version(self):
        task = self.task()
        change_coating(task.pk, self.line.pk, self.user, 'z140', 0, 0, 0)
        change_coating(task.pk, self.line.pk, self.user, 'z275', 0, 0, 1)
        with self.assertRaises(ProductionConflict):
            change_coating(task.pk, self.line.pk, self.user, 'z140', 0, 0, 0)

    def test_automatic_counter_records_material_on_each_side_of_change(self):
        task = self.task(sensor_true=True)
        self.assertEqual(arduino_data(self.request({'data': '1', 'line_id': 1})).status_code, 200)
        change_coating(task.pk, self.line.pk, self.user, 'z140', 1, 1, 0)
        self.assertEqual(arduino_data(self.request({'data': '1', 'line_id': 1})).status_code, 200)
        self.assertEqual(list(task.history_profile_records.order_by('id').values_list('coating_thickness', flat=True)), ['z275', 'z140'])
        self.assertEqual(list(task.profile_records.order_by('id').values_list('user_id', flat=True)), [self.user.pk, self.user.pk])

    def test_stock_is_idempotent_inherits_current_material_and_has_no_duplicate_strips(self):
        task = self.task()
        task = change_coating(task.pk, self.line.pk, self.user, 'z140', 120, 0, 0)
        task.history_offs_shtrips.create(value=500, type_value_id=self.kg, coating_thickness='z140')
        finish_task(task.pk, self.line.pk, self.user, 120, 120, 1)
        child = decide_stock(task.pk, self.line.pk, self.user, True, 6)
        retry = decide_stock(task.pk, self.line.pk, self.user, True, 6)
        self.assertEqual(child.pk, retry.pk)
        self.assertEqual(Tasks.objects.filter(stock_source=task).count(), 1)
        self.assertEqual((child.task_profile_type_id, child.task_profile_material, child.task_coating_type_id, child.task_coating_thickness), (task.task_profile_type_id, 1.2, self.paint.pk, 'z140'))
        self.assertEqual((child.task_profile_length, child.task_profile_amount, child.task_status_id), (6, 0, 3))
        self.assertEqual(child.order_label, 'На склад')
        self.assertIsNone(child.task_time_settingUp)
        self.assertFalse(child.allow_stock)
        self.assertFalse(child.history_offs_shtrips.exists())
        self.assertEqual(child.events.get(type_event_id=3).user_id, self.user.pk)
        record_total(child, 25, self.second)
        finish_task(child.pk, self.line.pk, self.second, 25, 25, 0)
        DatabaseWork({}).add_data_to_user_analytics(self.second.pk, child.pk)
        self.assertEqual(WorkerAnalyticsRecord.objects.get(task=child, user=self.second).profile_amount, 25)
        start, end = timezone.now() - timedelta(days=1), timezone.now() + timedelta(days=1)
        groups = _build_report_rows(_get_completed_tasks(start, end, self.user))
        stock_groups = [g for g in groups if g['order_number'] == 'На склад']
        self.assertEqual(sum(stock_groups[0]['profile_by_shift'].values()), 25)
        self.assertEqual(sum(sum(g['shtrips_by_shift'].values()) for g in groups), 500)

    def test_stock_decline_and_busy_line_prevent_creation(self):
        task = self.task(task_status_id=2)
        self.task()
        with self.assertRaises(ProductionConflict):
            decide_stock(task.pk, self.line.pk, self.user, True, 3)
        self.assertIsNone(decide_stock(task.pk, self.line.pk, self.user, False))
        with self.assertRaises(ProductionConflict):
            decide_stock(task.pk, self.line.pk, self.user, True, 3)
        self.assertFalse(Tasks.objects.filter(stock_source=task).exists())

    def test_stock_requires_permission_on_source_and_valid_length(self):
        task = self.task(task_status_id=2, allow_stock=False)
        with self.assertRaises(ProductionConflict):
            decide_stock(task.pk, self.line.pk, self.user, True, 3)
        task.allow_stock = True
        task.save()
        for length in (0, -1, float('nan'), float('inf'), None):
            with self.subTest(length=length), self.assertRaises(ValueError):
                decide_stock(task.pk, self.line.pk, self.user, True, length)

    def test_http_validation_conflicts_and_completion_response(self):
        task = self.task()
        data = dict(id_task=task.pk, coating='z140', total=120, expected_total=0, revision=0)
        self.assertEqual(update_coating(self.request(data)).status_code, 200)
        self.assertEqual(update_coating(self.request(data)).status_code, 409)
        data.update(revision=1, expected_total=120, total=200)
        response = complete_production(self.request(data))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)['pending_stock'])
        self.assertEqual(complete_production(self.request(data)).status_code, 200)
        self.assertEqual(task.events.filter(type_event_id=8).count(), 1)
        self.assertEqual(stock_decision(self.request({'id_task': task.pk, 'decision': 'yes', 'length': 'bad'})).status_code, 400)
        self.assertEqual(stock_decision(self.request({'id_task': task.pk, 'decision': 'yes', 'length': 3})).status_code, 200)

    def test_cross_line_coating_update_is_rejected(self):
        other_line = Workplace.objects.create(workplace_name='Other', type_of_equipment='Line', inv_number=2)
        task = self.task(task_workplace=other_line)
        response = update_coating(self.request(dict(id_task=task.pk, coating='z140', total=0, expected_total=0, revision=0)))
        self.assertEqual(response.status_code, 404)

    def test_failed_event_rolls_back_counter_and_material(self):
        task = self.task()
        with patch('master.production.write_event', side_effect=RuntimeError('storage failure')):
            with self.assertRaises(RuntimeError):
                change_coating(task.pk, self.line.pk, self.user, 'z140', 120, 0, 0)
        task.refresh_from_db()
        self.assertEqual((task.profile_amount_now, task.task_coating_thickness), (0, 'z275'))
        self.assertFalse(task.history_profile_records.exists())
