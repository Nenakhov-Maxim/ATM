from datetime import date
from pathlib import Path
from unittest.mock import patch

from django.template import Context, Engine
from django.test import RequestFactory, TestCase

from login.models import ProductionArea, User, Workplace
from .models import ProfileType, Tasks, TaskStatus, TypeEvent
from .shifts import shift_bounds
from .views import master_home


class HistoryDisplayTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        area = ProductionArea.objects.create(production_area_name='Test')
        cls.master = User.objects.create(username='master', is_superuser=True, production_area_id=area)
        cls.first = User.objects.create(username='worker-first', last_name='Иванов', first_name='Иван')
        cls.second = User.objects.create(username='worker-second', last_name='Петров', first_name='Пётр')
        line = Workplace.objects.create(workplace_name='Line', type_of_equipment='Line', inv_number=1, production_area_id=area)
        profile = ProfileType.objects.create(profile_name='Profile')
        TaskStatus.objects.create(pk=3, status_name='Running')
        TypeEvent.objects.create(pk=3, type_name='Принято рабочим', color='#000000')
        TypeEvent.objects.create(pk=7, type_name='Выполнена пересменка', color='#000000')
        start, end = shift_bounds(date(2026, 9, 15), 2)
        cls.task = Tasks.objects.create(task_name='Task', task_profile_type=profile, task_workplace=line,
                                       task_profile_amount=2000, task_profile_length=3, task_status_id=3,
                                       task_timedate_start=start, task_timedate_end=end, task_timedate_start_fact=start)
        cls.template = Engine(
            dirs=[str(Path(__file__).resolve().parent.parent / 'app' / 'templates')],
            libraries={'static': 'django.templatetags.static', 'split_tag': 'master.templatetags.split_tag',
                       'tags': 'worker.templatetags.tags'},
        ).get_template('master.html')

    def render_history(self):
        request = RequestFactory().get('/master/')
        request.user = self.master
        with patch('master.views.render') as render:
            master_home(request)
        tasks = render.call_args.args[2]['tasks']
        with self.assertNumQueries(3):
            tasks = list(tasks)
        # Rendering authors must use the prefetched users, not one query per event.
        with patch('django.urls.reverse', return_value='/'), self.assertNumQueries(0):
            return self.template.render(Context({'user': self.master, 'tasks': tasks}))

    def test_each_event_keeps_its_own_worker_after_handover(self):
        for user, event_type, message in ((self.first, 3, 'Start'), (self.first, 7, 'Handover'), (self.second, 3, 'Resume')):
            self.task.history_event_messages.create(user=user, type_event_id=event_type, message=message)
        html = self.render_history()
        self.assertEqual(html.count('<strong>Иванов Иван</strong>'), 2)
        self.assertEqual(html.count('<strong>Петров Пётр</strong>'), 1)
        self.assertIn('Handover', html)

    def test_legacy_event_without_user_is_not_attributed_to_current_worker(self):
        self.task.history_event_messages.create(user=None, type_event_id=7, message='Legacy handover')
        html = self.render_history()
        self.assertIn('<strong>Неизвестный пользователь</strong>', html)
        self.assertNotIn('<strong>master</strong>', html)

    def test_missing_name_uses_login_and_html_in_name_is_escaped(self):
        self.task.history_event_messages.create(user=self.master, type_event_id=3, message='Start')
        self.first.last_name = '<script>unsafe</script>'
        self.first.save(update_fields=['last_name'])
        self.task.history_event_messages.create(user=self.first, type_event_id=7, message='Handover')
        html = self.render_history()
        self.assertIn('<strong>master</strong>', html)
        self.assertIn('&lt;script&gt;unsafe&lt;/script&gt; Иван', html)
        self.assertNotIn('<script>unsafe</script>', html)
