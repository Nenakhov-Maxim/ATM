import json

from django.test import RequestFactory, TestCase

from login.models import ProductionArea, User
from .models import Tasks, TaskStatus
from .views import hide_task


class BulkHideTests(TestCase):
    def setUp(self):
        self.area = ProductionArea.objects.create(production_area_name='Test')
        self.user = User.objects.create(username='master', is_superuser=True, production_area_id=self.area)
        TaskStatus.objects.create(pk=2, status_name='Выполнено')
        TaskStatus.objects.create(pk=1, status_name='Создана')
        self.first = self.task()
        self.second = self.task()

    def task(self, **kwargs):
        values = dict(task_name='Test', task_profile_amount=10, task_status_id=2, production_area=self.area)
        values.update(kwargs)
        return Tasks.objects.create(**values)

    def post(self, payload):
        request = RequestFactory().post('/master/hide_task/', json.dumps(payload), content_type='application/json')
        request.user = self.user
        return hide_task(request)

    def test_bulk_hides_without_deleting_records(self):
        response = self.post({'id_tasks': [self.first.pk, self.second.pk]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Tasks.objects.count(), 2)
        self.assertFalse(Tasks.objects.filter(task_is_vision=True).exists())

    def test_single_task_still_supported(self):
        self.assertEqual(self.post({'id_task': str(self.first.pk)}).status_code, 200)
        self.second.refresh_from_db()
        self.assertTrue(self.second.task_is_vision)

    def test_invalid_selection_changes_nothing(self):
        other_area = ProductionArea.objects.create(production_area_name='Other')
        for task in [self.task(task_status_id=1), self.task(production_area=other_area)]:
            with self.subTest(task=task.pk):
                self.assertEqual(self.post({'id_tasks': [self.first.pk, task.pk]}).status_code, 400)
                self.first.refresh_from_db()
                self.assertTrue(self.first.task_is_vision)

    def test_invalid_input(self):
        for ids in [[], '1', [True], ['bad'], [999999]]:
            with self.subTest(ids=ids):
                self.assertEqual(self.post({'id_tasks': ids}).status_code, 400)

    def test_permission_required(self):
        from django.core.exceptions import PermissionDenied
        self.user.is_superuser = False
        with self.assertRaises(PermissionDenied):
            self.post({'id_tasks': [self.first.pk]})
