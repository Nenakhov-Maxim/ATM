import math

from django.db import transaction
from django.utils import timezone
from login.models import Workplace

from .models import Tasks, TaskEvent, TaskProfileRecord
from .history_utils import infer_profile_record_user
from .shifts import production_shift_at, shift_bounds


class ProductionConflict(ValueError):
    pass


@transaction.atomic
def begin_task(task_id, line_id, user, revision=None):
    Workplace.objects.select_for_update().get(pk=line_id)
    task = Tasks.objects.select_for_update().get(pk=task_id, task_workplace_id=line_id)
    if task.task_status_id == 3:
        operator = infer_profile_record_user(task)
        if operator and operator.pk != user.pk:
            raise ProductionConflict('Задание уже выполняет другой рабочий. Сначала нужна пересменка.')
        return task
    if revision is not None and revision != task.coating_revision:
        raise ProductionConflict('Состояние задания изменилось. Обновите страницу перед началом работы.')
    if task.task_status_id not in (4, 6, 7, 8):
        raise ProductionConflict('Задание недоступно для начала выполнения.')
    if Tasks.objects.filter(task_workplace_id=line_id, task_status_id__in=[3, 7]).exclude(pk=task.pk).exists():
        raise ProductionConflict('На линии уже выполняется другое задание.')
    resumed = task.task_timedate_start_fact is not None
    if not resumed:
        task.task_timedate_start_fact = timezone.now()
    task.task_status_id = 3
    # The revision also invalidates counter requests from the previous operator.
    task.coating_revision += 1
    task.save(update_fields=['task_status_id', 'task_timedate_start_fact', 'coating_revision'])
    write_event(task, user, 3, f'{"Продолжено" if resumed else "Начато"} изготовление. Общий счётчик: {task.profile_amount_now} шт.')
    return task


@transaction.atomic
def hand_over_task(task_id, line_id, user, total, expected_total, revision):
    task = Tasks.objects.select_for_update().get(pk=task_id, task_workplace_id=line_id)
    if task.task_status_id == 8:
        event = task.events.filter(type_event_id=7).order_by('-created_at', '-id').first()
        if event and event.user_id == user.pk and task.profile_amount_now == total:
            return task
        raise ProductionConflict('Задание уже передано на пересменку.')
    if task.task_status_id != 3:
        raise ProductionConflict('Передать на пересменку можно только выполняемое задание.')
    check_counter_version(task, expected_total, revision)
    operator = infer_profile_record_user(task)
    if operator and operator.pk != user.pk:
        raise ProductionConflict('Пересменку должен подтвердить рабочий, выполняющий задание.')
    record_total(task, total, user)
    task.task_status_id = 8
    task.coating_revision += 1
    task.save(update_fields=['task_status_id', 'coating_revision'])
    write_event(task, user, 7, f'Пересменка. Общий счётчик: {task.profile_amount_now} шт.')
    return task


def write_event(task, user, type_id, message):
    timestamp = timezone.now()
    data = dict(user=user, type_event_id=type_id, message=message[:500], created_at=timestamp)
    task.history_event_messages.create(**data)
    TaskEvent.objects.create(task=task, **data)


def record_output(task, amount, user, timestamp=None):
    """Caller holds the task lock; both histories get the same material snapshot."""
    data = dict(
        user=user, amount=amount, profile_sum=task.profile_amount_now,
        created_at=timestamp or timezone.now(),
        coating_thickness=task.task_coating_thickness or '',
    )
    task.history_profile_records.create(**data)
    TaskProfileRecord.objects.create(task=task, **data)


def record_total(task, value, user):
    try:
        total = int(str(value))
    except (TypeError, ValueError):
        raise ValueError('Количество должно быть целым неотрицательным числом.')
    if total < max(0, task.coating_start_amount):
        raise ValueError('Количество не может быть меньше счётчика на момент смены покрытия.')
    delta = total - task.profile_amount_now
    if delta:
        task.profile_amount_now = total
        task.last_update = timezone.now()
        record_output(task, delta, user, task.last_update)
        task.save(update_fields=['profile_amount_now', 'last_update'])


def set_coating(task, coating):
    if coating == task.task_coating_thickness:
        return
    # Freeze legacy rows before changing the fallback used by old reports.
    old = task.task_coating_thickness or ''
    task.history_profile_records.filter(coating_thickness__isnull=True).update(coating_thickness=old)
    task.profile_records.filter(coating_thickness__isnull=True).update(coating_thickness=old)
    task.history_offs_shtrips.filter(coating_thickness__isnull=True).update(coating_thickness=old)
    task.task_coating_thickness = coating
    task.coating_revision += 1
    task.coating_start_amount = task.profile_amount_now
    task.save(update_fields=['task_coating_thickness', 'coating_revision', 'coating_start_amount'])


def check_counter_version(task, expected_total, revision):
    if task.profile_amount_now != expected_total or task.coating_revision != revision:
        raise ProductionConflict('Счётчик или покрытие изменились. Обновите данные и подтвердите снова.')


@transaction.atomic
def change_coating(task_id, line_id, user, coating, total, expected_total, revision):
    task = Tasks.objects.select_for_update().get(pk=task_id, task_workplace_id=line_id)
    if task.task_status_id != 3:
        raise ProductionConflict('Покрытие можно менять только в выполняемом задании.')
    check_counter_version(task, expected_total, revision)
    old = task.task_coating_thickness or ''
    if not coating or len(coating) > 100:
        raise ValueError('Укажите базовое покрытие, не более 100 символов.')
    if int(total) < task.profile_amount_now:
        raise ValueError('При смене покрытия нельзя уменьшить общее количество.')
    record_total(task, total, user)
    set_coating(task, coating)
    if old != coating:
        write_event(task, user, 9, f'Базовое покрытие: {old or "без покрытия"} -> {coating}. Общий счётчик: {task.profile_amount_now} шт.')
    return task


@transaction.atomic
def finish_task(task_id, line_id, user, total, expected_total, revision):
    task = Tasks.objects.select_for_update().get(pk=task_id, task_workplace_id=line_id)
    if task.task_status_id == 2:
        return task
    if task.task_status_id != 3:
        raise ProductionConflict('Можно завершить только выполняемое задание.')
    check_counter_version(task, expected_total, revision)
    record_total(task, total, user)
    task.task_status_id = 2
    task.task_timedate_end_fact = timezone.now()
    task.sensor_true = False
    task.save(update_fields=['task_status_id', 'task_timedate_end_fact', 'sensor_true'])
    write_event(task, user, 8, f'Задание завершено. Изготовлено: {task.profile_amount_now} шт.')
    return task


@transaction.atomic
def decide_stock(task_id, line_id, user, make_stock, length=None):
    # Lock the line too: two pending orders must not start two stock jobs.
    Workplace.objects.select_for_update().get(pk=line_id)
    source = Tasks.objects.select_for_update().get(pk=task_id, task_workplace_id=line_id)
    existing = Tasks.objects.filter(stock_source_id=source.pk).first()
    if existing:
        return existing
    if source.task_status_id != 2 or not source.allow_stock or source.stock_source_id:
        raise ProductionConflict('Доработка на склад для этого задания недоступна.')
    if source.stock_decision is not None:
        if not make_stock and not source.stock_decision:
            return None
        raise ProductionConflict('Решение по этому заданию уже принято.')
    if not make_stock:
        source.stock_decision = False
        source.save(update_fields=['stock_decision'])
        write_event(source, user, 9, 'Доработка штрипса на склад не требуется.')
        return None
    if Tasks.objects.filter(task_workplace_id=line_id, task_status_id__in=[3, 7]).exists():
        raise ProductionConflict('На линии уже выполняется другое задание.')
    if length is None or not math.isfinite(length) or length <= 0:
        raise ValueError('Длина должна быть положительным числом.')
    now = timezone.now()
    day, shift = production_shift_at(now)
    start, end = shift_bounds(day, shift)
    child = Tasks.objects.create(
        stock_source=source, task_order_number='На склад', task_name='Изготовить профиль на склад',
        task_profile_type=source.task_profile_type, task_profile_material=source.task_profile_material,
        task_coating_thickness=source.task_coating_thickness, task_coating_type=source.task_coating_type,
        task_coating_area=source.task_coating_area, task_profile_length=length, task_profile_amount=0,
        task_workplace=source.task_workplace, production_area=source.production_area,
        task_status_id=3, task_timedate_start_fact=now,
        task_shift_date=day, task_shift=shift, task_timedate_start=start, task_timedate_end=end,
        task_user_created_by=user, task_user_created=f'{user.last_name} {user.first_name}'.strip() or user.username,
    )
    write_event(child, user, 1, f'Доработка остатка штрипса из задания № {source.pk}. До окончания остатка.')
    write_event(child, user, 3, 'Начато изготовление на склад без переналадки.')
    write_event(source, user, 9, f'Создано складское задание № {child.pk}, длина {length} м.')
    source.stock_decision = True
    source.save(update_fields=['stock_decision'])
    return child
