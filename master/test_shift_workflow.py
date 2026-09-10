import asyncio
import json
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from asgiref.sync import async_to_sync
from django.contrib.auth.signals import user_logged_in
from django.test import RequestFactory, TestCase

from login.models import ProductionArea, User, Workplace
from worker.production_views import handover_production
from worker.task_feed import ShiftTaskFeedConsumer
from .databaseWork import DatabaseWork
from .history_utils import infer_profile_record_user
from .models import Tasks, TaskStatus, TypeEvent, ProfileType
from .production import begin_task, hand_over_task, ProductionConflict, record_total
from .shift_selection import login_shift, worker_selection, worker_shift_tasks, with_effective_shift
from .shifts import shift_bounds
from .views import master_home


DAY = date(2026, 9, 10)


class ShiftLoginTests(TestCase):
    def test_shift_is_frozen_until_each_new_login_including_same_user(self):
        request = RequestFactory().get('/')
        request.session = {}
        user = User.objects.create(username='login-worker')
        for shift in (1, 2, 3):
            now = shift_bounds(DAY, shift)[0] + timedelta(hours=1)
            with patch('master.shift_selection.timezone.now', return_value=now):
                user_logged_in.send(sender=User, request=request, user=user)
                self.assertEqual(worker_selection(request.session, {}), (DAY, shift))
            later = shift_bounds(DAY + timedelta(days=1), 2)[0]
            with patch('master.shift_selection.timezone.now', return_value=later):
                self.assertEqual(worker_selection(request.session, {}), (DAY, shift))
                self.assertEqual(login_shift(request.session), (DAY, shift))

    def test_manual_tab_and_date_persist_but_do_not_change_login_shift(self):
        session = {'production_login_shift': {'date': DAY.isoformat(), 'shift': 1}}
        selected = {'production_date': '2026-09-11', 'shift': '3'}
        self.assertEqual(worker_selection(session, selected), (DAY + timedelta(days=1), 3))
        self.assertEqual(worker_selection(session, {}), (DAY + timedelta(days=1), 3))
        self.assertEqual(login_shift(session), (DAY, 1))
        self.assertEqual(worker_selection(session, {'shift': 'bad'}), (DAY, 1))


class ShiftWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.area = ProductionArea.objects.create(production_area_name='Test')
        cls.line = Workplace.objects.create(pk=1, workplace_name='Line', type_of_equipment='Line', inv_number=1, production_area_id=cls.area)
        cls.user = User.objects.create(username='first', is_superuser=True, production_area_id=cls.area)
        cls.other = User.objects.create(username='second', is_superuser=True, production_area_id=cls.area)
        cls.profile = ProfileType.objects.create(profile_name='Test profile')
        for pk in range(1, 10):
            TaskStatus.objects.create(pk=pk, status_name=str(pk))
            TypeEvent.objects.create(pk=pk, type_name=str(pk), color='#000000')

    def task(self, shift=1, day=DAY, **changes):
        start, end = shift_bounds(day, shift)
        fields = dict(task_name='Task', task_workplace=self.line, task_profile_type=self.profile,
                      task_profile_amount=200, task_profile_length=3, task_status_id=4,
                      task_shift_date=day, task_shift=shift, task_timedate_start=start, task_timedate_end=end)
        fields.update(changes)
        return Tasks.objects.create(**fields)

    def selected(self, shift, login=1):
        return worker_shift_tasks(Tasks.objects.filter(task_workplace=self.line), DAY, shift, DAY, login)

    def test_legacy_boundaries_match_explicit_shift_and_previous_day(self):
        for shift in (1, 2, 3):
            start, end = shift_bounds(DAY, shift)
            for value in (start, end - timedelta(microseconds=1)):
                task = self.task(task_shift=None, task_shift_date=None, task_timedate_start=value)
                row = with_effective_shift(Tasks.objects.filter(pk=task.pk)).get()
                self.assertEqual((row.effective_shift_date, row.effective_shift), (DAY, shift))
                self.assertIn(f'{shift} смена', task.planned_shift_label)
        explicit = self.task(shift=3, task_timedate_start=shift_bounds(DAY, 1)[0])
        row = with_effective_shift(Tasks.objects.filter(pk=explicit.pk)).get()
        self.assertEqual(row.effective_shift, 3)

    def test_tabs_keep_overdue_and_started_first_without_future_leaks(self):
        backlog = self.task(day=DAY - timedelta(days=1))
        running = self.task(shift=1, task_status_id=3)
        paused = self.task(task_status_id=6)
        handover = self.task(task_status_id=8)
        selected = [self.task(shift=shift) for shift in (1, 2, 3)]
        self.task(task_status_id=2)
        self.task(task_status_id=1)
        self.task(day=DAY + timedelta(days=1))
        for shift in (1, 2, 3):
            rows = list(self.selected(shift))
            self.assertEqual({row.pk for row in rows}, {backlog.pk, running.pk, paused.pk, handover.pk, selected[shift-1].pk})
            self.assertEqual(rows[-1].pk, selected[shift-1].pk)
            self.assertTrue(all(row.shift_priority == 0 for row in rows[:-1]))
        second_login = list(self.selected(2, login=2))
        self.assertIn(selected[0].pk, [row.pk for row in second_login])

    def test_unknown_schedule_remains_visible_and_date_filter_works(self):
        task = self.task(task_shift=None, task_shift_date=None, task_timedate_start=None)
        self.assertIn(task.pk, self.selected(3).values_list('id', flat=True))
        self.assertFalse(with_effective_shift(Tasks.objects.filter(pk=task.pk)).filter(effective_shift=1).exists())

    def test_handover_saves_boundary_for_first_worker_and_preserves_original_start(self):
        task = self.task()
        start = shift_bounds(DAY, 1)[0] + timedelta(hours=2)
        with patch('master.production.timezone.now', return_value=start):
            task = begin_task(task.pk, self.line.pk, self.user)
        record_total(task, 100, self.user)
        task = hand_over_task(task.pk, self.line.pk, self.user, 120, 100, task.coating_revision)
        self.assertEqual((task.profile_amount_now, task.task_status_id), (120, 8))
        self.assertEqual(list(task.profile_records.order_by('id').values_list('amount', 'user_id')), [(100, self.user.pk), (20, self.user.pk)])
        self.assertEqual(task.events.filter(type_event_id=7).count(), 1)
        self.assertEqual(task.history_event_messages.filter(type_event_id=7).count(), 1)
        task = begin_task(task.pk, self.line.pk, self.other)
        self.assertEqual(task.task_timedate_start_fact, start)
        self.assertEqual(infer_profile_record_user(task), self.other)
        record_total(task, 200, self.other)
        self.assertEqual(task.profile_records.filter(user=self.other).get().amount, 80)

    def test_repeated_begin_is_idempotent_and_cannot_change_worker(self):
        task = begin_task(self.task().pk, self.line.pk, self.user)
        repeat = begin_task(task.pk, self.line.pk, self.user)
        self.assertEqual((repeat.task_timedate_start_fact, repeat.coating_revision), (task.task_timedate_start_fact, task.coating_revision))
        self.assertEqual(task.events.filter(type_event_id=3).count(), 1)
        with self.assertRaises(ProductionConflict):
            begin_task(task.pk, self.line.pk, self.other)
        self.assertEqual(task.events.filter(type_event_id=3).count(), 1)

    def test_legacy_operator_is_respected_without_normalized_events(self):
        task = self.task(task_status_id=3)
        task.history_event_messages.create(type_event_id=3, user=self.user, message='Legacy start')
        with self.assertRaises(ProductionConflict):
            begin_task(task.pk, self.line.pk, self.other)
        with self.assertRaises(ProductionConflict):
            hand_over_task(task.pk, self.line.pk, self.other, 120, 0, 0)
        self.assertFalse(task.profile_records.exists())

    def test_master_filter_combines_date_and_shift_for_new_and_legacy_tasks(self):
        explicit = self.task(shift=2)
        legacy = self.task(shift=2, task_shift=None, task_shift_date=None)
        self.task(shift=1)
        self.task(shift=2, day=DAY - timedelta(days=1))
        request = RequestFactory().get('/master/', {'production_date': DAY.isoformat(), 'shift': 2})
        request.user = self.user
        with patch('master.views.render') as render:
            master_home(request)
        tasks = render.call_args.args[2]['tasks']
        self.assertEqual(set(tasks.values_list('id', flat=True)), {explicit.pk, legacy.pk})

    def test_handover_retry_and_stale_counters_do_not_duplicate_or_cross_workers(self):
        task = begin_task(self.task().pk, self.line.pk, self.user)
        revision = task.coating_revision
        hand_over_task(task.pk, self.line.pk, self.user, 120, 0, revision)
        hand_over_task(task.pk, self.line.pk, self.user, 120, 0, revision)
        self.assertEqual(task.events.filter(type_event_id=7).count(), 1)
        self.assertFalse(DatabaseWork({}).change_profile_amount(task.pk, 150, self.user, revision))
        with self.assertRaises(ProductionConflict):
            begin_task(task.pk, self.line.pk, self.user, revision=revision - 1)
        begin_task(task.pk, self.line.pk, self.other)
        with self.assertRaises(ProductionConflict):
            hand_over_task(task.pk, self.line.pk, self.user, 120, 0, revision)
        self.assertFalse(DatabaseWork({}).change_profile_amount(task.pk, 150, self.user, revision))

    def test_handover_rolls_back_if_history_write_fails(self):
        task = begin_task(self.task().pk, self.line.pk, self.user)
        with patch('master.production.write_event', side_effect=RuntimeError('failure')):
            with self.assertRaises(RuntimeError):
                hand_over_task(task.pk, self.line.pk, self.user, 120, 0, task.coating_revision)
        task.refresh_from_db()
        self.assertEqual((task.task_status_id, task.profile_amount_now), (3, 0))
        self.assertFalse(task.profile_records.exists())

    def test_backlog_is_priority_not_a_block_on_other_tasks(self):
        self.task(day=DAY - timedelta(days=1), task_status_id=8)
        task = begin_task(self.task(shift=2).pk, self.line.pk, self.user)
        self.assertEqual(task.task_status_id, 3)

    def test_handover_endpoint_requires_valid_counter_and_line(self):
        task = begin_task(self.task().pk, self.line.pk, self.user)
        def post(data, user=self.user):
            request = RequestFactory().post('/worker/shiftChange/', data=json.dumps(data), content_type='application/json')
            request.user = user
            return handover_production(request)
        self.assertEqual(post({'id_task': task.pk, 'profile_amount': 120}).status_code, 400)
        data = dict(id_task=task.pk, total=120, expected_total=0, revision=task.coating_revision)
        self.assertEqual(post(data, self.other).status_code, 409)
        self.assertEqual(post(data).status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.profile_amount_now, 120)

    def test_feed_uses_same_selection_and_one_query(self):
        self.task(day=DAY - timedelta(days=1))
        self.task(shift=1)
        self.task(shift=2)
        consumer = ShiftTaskFeedConsumer()
        consumer.line_id = self.line.pk
        consumer.day, consumer.shift = DAY, 1
        consumer.login_day, consumer.login_shift_number = DAY, 1
        with self.assertNumQueries(1):
            rows = vars(ShiftTaskFeedConsumer)['snapshot'].func(consumer)
        self.assertEqual([row['id'] for row in rows], list(self.selected(1).values_list('id', flat=True)))

    def test_feed_rejects_anonymous_and_other_production_area(self):
        from django.contrib.auth.models import AnonymousUser
        consumer = ShiftTaskFeedConsumer()
        consumer.line_id = self.line.pk
        consumer.scope = {'user': AnonymousUser()}
        self.assertFalse(vars(ShiftTaskFeedConsumer)['allowed'].func(consumer))
        user = User.objects.create(username='outside')
        consumer.scope = {'user': user}
        with patch.object(user, 'has_perm', return_value=True):
            self.assertFalse(vars(ShiftTaskFeedConsumer)['allowed'].func(consumer))

    def test_feed_status_or_schedule_changes_trigger_refresh(self):
        async def scenario():
            consumer = ShiftTaskFeedConsumer()
            consumer.snapshot = AsyncMock(side_effect=[
                [{'id': 1, 'task_status_id': 4, 'effective_shift': 1, 'profile_amount_now': 0, 'sensor_true': False}],
                [],
            ])
            consumer.send_json = AsyncMock()
            with patch('worker.task_feed.asyncio.sleep', new=AsyncMock(side_effect=[None, asyncio.CancelledError])):
                with self.assertRaises(asyncio.CancelledError):
                    await consumer.poll({'1': '4'})
            consumer.send_json.assert_awaited_once_with({'type': 'tasks_changed'})
        async_to_sync(scenario)()
