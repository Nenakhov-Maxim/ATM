import importlib
import json
from unittest.mock import patch

from django.apps import apps
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection
from django.http import Http404
from django.test import RequestFactory, TestCase, TransactionTestCase

from login.models import ProductionArea, User, Workplace, UserDepPosition
from .access import area_ids_for, task_area_query
from .forms import NewTaskForm, EditTaskForm
from .models import Tasks, TaskStatus, ProfileType, TypeEvent
from .views import new_task, master_home, start_task, pause_task, edit_task, delete_task, hide_task, new_report


class AreaAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.areas = [ProductionArea.objects.create(production_area_name=name) for name in ('Профильный', 'Штамповка', 'Чужой')]
        position = UserDepPosition.objects.create(position='Мастер')
        cls.user = User.objects.create(username='master', production_area_id=cls.areas[0], position_id=position)
        cls.user.user_permissions.add(*Permission.objects.filter(content_type__app_label='master'))
        cls.user.available_areas.add(cls.areas[1])
        cls.lines = [Workplace.objects.create(workplace_name=f'Line {i}', inv_number=i, type_of_equipment='Line', production_area_id=area) for i, area in enumerate(cls.areas)]
        cls.profile = ProfileType.objects.create(profile_name='ПК')
        for status in (1, 2, 4):
            TaskStatus.objects.create(pk=status, status_name=str(status))
        TypeEvent.objects.create(pk=2, type_name='Отправлена', color='#000000')
        cls.tasks = [Tasks.objects.create(task_name=f'Task {i}', task_profile_amount=100, task_workplace=line, task_status_id=4) for i, line in enumerate(cls.lines)]

    def request(self, method='post', data=None, json_body=True):
        factory = RequestFactory()
        if method == 'get':
            req = factory.get('/master/', data or {})
        elif json_body:
            req = factory.post('/master/', json.dumps(data or {}), content_type='application/json')
        else:
            req = factory.post('/master/', data or {})
        req.user = self.user
        return req

    def test_primary_and_additional_areas(self):
        self.assertEqual(area_ids_for(self.user), {self.areas[0].pk, self.areas[1].pk})
        self.assertCountEqual(Tasks.objects.filter(task_area_query(self.user)), self.tasks[:2])
        self.user.available_areas.clear()
        self.assertEqual(area_ids_for(self.user), {self.areas[0].pk})
        self.user.production_area_id = None
        self.assertEqual(area_ids_for(self.user), set())
        self.assertFalse(Tasks.objects.filter(task_area_query(self.user)).exists())

    def test_form_cannot_bypass_area_by_submitting_workplace_id(self):
        for form_class in (NewTaskForm, EditTaskForm):
            form = form_class(user=self.user, initial={'task_workplace': self.lines[2].pk})
            self.assertCountEqual(form.fields['task_workplace'].queryset, self.lines[:2])
            with self.assertRaises(ValidationError):
                form.fields['task_workplace'].clean(self.lines[2].pk)
            self.assertEqual(form.fields['task_workplace'].clean(self.lines[1].pk), self.lines[1])

    def test_form_rejects_area_workplace_mismatch(self):
        form = NewTaskForm({'task_area': self.areas[0].pk, 'task_workplace': self.lines[1].pk}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('Рабочее место не относится', str(form.errors['task_workplace']))

    def test_home_filter_and_foreign_area(self):
        for area, expected in [(None, self.tasks[:2]), (self.areas[1].pk, [self.tasks[1]])]:
            with patch('master.views.render') as render:
                master_home(self.request('get', {'area': area} if area else {}))
                self.assertCountEqual(render.call_args.args[2]['tasks'], expected)
        with self.assertRaises(PermissionDenied):
            master_home(self.request('get', {'area': self.areas[2].pk}))

    def test_each_single_action_denies_foreign_task(self):
        for view in (start_task, delete_task, hide_task):
            with self.subTest(view=view.__name__), self.assertRaises(Http404):
                view(self.request(data={'id_task': self.tasks[2].pk}))
        with self.assertRaises(Http404):
            edit_task(self.request('get', {'id_task': self.tasks[2].pk}))
        with self.assertRaises(Http404):
            edit_task(self.request(data={'id_task': self.tasks[2].pk}, json_body=False))
        with self.assertRaises(Http404):
            pause_task(self.request(), self.tasks[2].pk)
        self.assertTrue(Tasks.objects.filter(pk=self.tasks[2].pk).exists())

    def test_additional_area_single_action(self):
        self.assertEqual(start_task(self.request(data={'id_task': self.tasks[1].pk})).status_code, 200)
        self.assertEqual(edit_task(self.request('get', {'id_task': self.tasks[1].pk})).status_code, 200)

    def test_bulk_delete_all_or_nothing_and_both_areas(self):
        response = delete_task(self.request(data={'id_tasks': [self.tasks[0].pk, self.tasks[2].pk]}))
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Tasks.objects.filter(pk=self.tasks[0].pk).exists())
        response = delete_task(self.request(data={'id_tasks': [t.pk for t in self.tasks[:2]]}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Tasks.objects.count(), 1)

    def test_bulk_hide_all_or_nothing_and_both_areas(self):
        Tasks.objects.update(task_status_id=2)
        response = hide_task(self.request(data={'id_tasks': [self.tasks[0].pk, self.tasks[2].pk]}))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Tasks.objects.filter(task_is_vision=True).count(), 3)
        response = hide_task(self.request(data={'id_tasks': [t.pk for t in self.tasks[:2]]}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Tasks.objects.count(), 3)
        self.assertEqual(Tasks.objects.filter(task_is_vision=True).count(), 1)

    def test_saved_area_cannot_grant_access_to_foreign_workplace(self):
        task = self.tasks[2]
        task.production_area = self.areas[0]
        task.save()
        self.assertFalse(Tasks.objects.filter(task_area_query(self.user), pk=task.pk).exists())
        task.task_workplace = None
        task.save()
        self.assertTrue(Tasks.objects.filter(task_area_query(self.user), pk=task.pk).exists())

    def test_report_rejects_foreign_area(self):
        data = {'area': self.areas[2].pk, 'report_mode': 'shifts', 'production_date': '2026-09-15', 'report_shifts': ['1']}
        with self.assertRaises(PermissionDenied):
            new_report(self.request(data=data, json_body=False))

    def test_seed_migration_is_idempotent_and_preserves_tasks(self):
        migration = importlib.import_module('login.migrations.0012_seed_available_areas')
        before = list(Tasks.objects.order_by('pk').values())
        with connection.schema_editor() as editor:
            migration.seed_areas(apps, editor)
            migration.seed_areas(apps, editor)
        self.assertCountEqual(self.user.available_areas.all(), self.areas[:2])
        self.assertEqual(before, list(Tasks.objects.order_by('pk').values()))

    def test_create_on_additional_area_and_reject_foreign_area(self):
        TypeEvent.objects.create(pk=1, type_name='Создана', color='#000000')
        payload = {
            'task_name': 'New', 'task_shift_date': '2026-09-15', 'task_shift': '1',
            'task_profile_type': self.profile.pk, 'task_profile_length': '3',
            'task_profile_amount': '100', 'task_order_number': 'Order', 'task_coating_type': '',
            'task_workplace': self.lines[1].pk, 'task_area': self.areas[1].pk,
        }
        self.assertEqual(new_task(self.request(data=payload, json_body=False)).status_code, 301)
        self.assertEqual(Tasks.objects.latest('pk').task_workplace_id, self.lines[1].pk)
        payload.update(task_workplace=self.lines[2].pk, task_area=self.areas[2].pk)
        self.assertEqual(new_task(self.request(data=payload, json_body=False)).status_code, 400)
        self.assertEqual(Tasks.objects.count(), 4)

    def test_analytics_includes_only_accessible_lines(self):
        from analytics.views import update_current_profile
        TaskStatus.objects.create(pk=3, status_name='Выполняется')
        Tasks.objects.update(task_status_id=3, profile_amount_now=5)
        data = update_current_profile(3, user=self.user)
        self.assertEqual(set(data), {f'{line.pk} линия' for line in self.lines[:2]})


class AreaMigrationTests(TransactionTestCase):
    def test_migration_adds_access_without_changing_existing_tasks(self):
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        executor.migrate([('login', '0010_workplace_production_area_id')])
        try:
            old_apps = executor.loader.project_state([('login', '0010_workplace_production_area_id')]).apps
            OldUser = old_apps.get_model('login', 'User')
            OldArea = old_apps.get_model('login', 'ProductionArea')
            area = OldArea.objects.create(production_area_name='Existing area')
            user = OldUser.objects.create(username='existing', production_area_id_id=area.pk)
            no_area = OldUser.objects.create(username='without-area')
            task = Tasks.objects.create(task_name='Existing task', production_area_id=area.pk, task_profile_amount=42, profile_amount_now=12)
            before = Tasks.objects.filter(pk=task.pk).values().get()
            executor = MigrationExecutor(connection)
            executor.migrate([('login', '0012_seed_available_areas')])
            self.assertEqual(list(User.objects.get(pk=user.pk).available_areas.values_list('pk', flat=True)), [area.pk])
            self.assertFalse(User.objects.get(pk=no_area.pk).available_areas.exists())
            self.assertEqual(Tasks.objects.filter(pk=task.pk).values().get(), before)
        finally:
            MigrationExecutor(connection).migrate([('login', '0012_seed_available_areas')])
