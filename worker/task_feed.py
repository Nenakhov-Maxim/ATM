import asyncio
from contextlib import suppress
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from login.models import Workplace
from master.models import Tasks
from master.shift_selection import login_shift, worker_selection, worker_shift_tasks


class ShiftTaskFeedConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.poll_task = None
        self.line_id = self.scope['url_route']['kwargs']['line_name']
        if not await self.allowed():
            await self.close(code=4403)
            return
        params = {key: values[-1] for key, values in parse_qs(self.scope['query_string'].decode()).items()}
        self.day, self.shift = worker_selection(self.scope['session'], params)
        self.login_day, self.login_shift_number = login_shift(self.scope['session'])
        await self.accept()
        await self.send_json({'type': 'Welcome'})

    @database_sync_to_async
    def allowed(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated or not user.has_perm('worker.change_workertypeproblem'):
            return False
        if user.is_superuser:
            return True
        area_id = user.production_area_id_id
        return bool(area_id) and Workplace.objects.filter(pk=self.line_id, production_area_id_id=area_id).exists()

    async def receive_json(self, content):
        if content.get('message') == 'start' and self.poll_task is None:
            initial = {str(key): str(value) for key, value in content.get('task_list', {}).items()}
            self.poll_task = asyncio.create_task(self.poll(initial))

    async def disconnect(self, code):
        if self.poll_task is not None:
            self.poll_task.cancel()
            with suppress(asyncio.CancelledError):
                await self.poll_task

    @database_sync_to_async
    def snapshot(self):
        tasks = worker_shift_tasks(
            Tasks.objects.filter(task_workplace_id=self.line_id),
            self.day, self.shift, self.login_day, self.login_shift_number,
        )
        return list(tasks.values(
            'id', 'task_status_id', 'coating_revision', 'task_name', 'task_order_number',
            'task_profile_length', 'task_profile_amount', 'task_profile_material',
            'task_coating_type_id', 'task_coating_thickness', 'task_coating_area',
            'task_profile_type_id', 'task_timedate_start', 'task_timedate_end',
            'effective_shift_date', 'effective_shift', 'shift_priority', 'allow_stock',
            'profile_amount_now', 'sensor_true',
        ))

    async def poll(self, initial):
        previous = None
        counters = {}
        while True:
            rows = await self.snapshot()
            signature = [{key: value for key, value in row.items() if key not in ('profile_amount_now', 'sensor_true')} for row in rows]
            statuses = {str(row['id']): str(row['task_status_id']) for row in rows}
            if (previous is None and statuses != initial) or (previous is not None and signature != previous):
                await self.send_json({'type': 'tasks_changed'})
            previous = signature
            for row in rows:
                if row['task_status_id'] != 3:
                    continue
                value = (row['profile_amount_now'], row['sensor_true'])
                if counters.get(row['id']) != value:
                    await self.send_json({'type': 'production_counter', 'content': {
                        'task_id': row['id'], 'total': value[0], 'sensor_true': value[1],
                    }})
                counters[row['id']] = value
            await asyncio.sleep(2)
