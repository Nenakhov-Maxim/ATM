from datetime import date, timedelta

from django.db.models import Case, DateField, DateTimeField, ExpressionWrapper, F, IntegerField, Q, Value, When
from django.db.models.functions import ExtractHour, TruncDate
from django.utils import timezone

from .shifts import PRODUCTION_TIME_ZONE, production_shift_at


def reset_login_shift(session):
    day, shift = production_shift_at(timezone.now())
    session['production_login_shift'] = {'date': day.isoformat(), 'shift': shift}
    session.pop('worker_shift_selection', None)


def login_shift(session):
    if 'production_login_shift' not in session:
        reset_login_shift(session)
    value = session['production_login_shift']
    return date.fromisoformat(value['date']), int(value['shift'])


def worker_selection(session, params):
    day, shift = login_shift(session)
    saved = session.get('worker_shift_selection', {})
    try:
        day = date.fromisoformat(params.get('production_date') or saved.get('date') or day.isoformat())
        shift = int(params.get('shift') or saved.get('shift') or shift)
        if shift not in (1, 2, 3):
            raise ValueError
    except (ValueError, TypeError):
        day, shift = login_shift(session)
    session['worker_shift_selection'] = {'date': day.isoformat(), 'shift': shift}
    return day, shift


def with_effective_shift(tasks):
    explicit = Q(task_shift__in=[1, 2, 3], task_shift_date__isnull=False)
    tasks = tasks.annotate(_plan_hour=ExtractHour('task_timedate_start', tzinfo=PRODUCTION_TIME_ZONE))
    # Subtract eight hours before taking the local date: 00:00-08:00 belong to yesterday.
    shifted_start = ExpressionWrapper(F('task_timedate_start') - timedelta(hours=8), output_field=DateTimeField())
    return tasks.annotate(
        effective_shift=Case(
            When(explicit, then=F('task_shift')),
            When(_plan_hour__gte=8, _plan_hour__lt=17, then=Value(1)),
            When(Q(_plan_hour__gte=17) | Q(_plan_hour__lt=1), then=Value(2)),
            When(task_timedate_start__isnull=False, then=Value(3)),
            default=Value(None), output_field=IntegerField(),
        ),
        effective_shift_date=Case(
            When(explicit, then=F('task_shift_date')),
            default=TruncDate(shifted_start, tzinfo=PRODUCTION_TIME_ZONE), output_field=DateField(),
        ),
    )


def worker_shift_tasks(tasks, day, shift, login_day, login_shift_number):
    tasks = with_effective_shift(tasks).filter(task_status_id__in=[3, 4, 6, 7, 8])
    overdue = Q(effective_shift_date__lt=login_day) | Q(
        effective_shift_date=login_day, effective_shift__lt=login_shift_number,
    )
    unfinished = Q(task_status_id__in=[3, 6, 7, 8]) | overdue | Q(effective_shift_date__isnull=True)
    selected = Q(effective_shift_date=day, effective_shift=shift)
    return tasks.filter(unfinished | selected).annotate(
        shift_priority=Case(When(unfinished, then=Value(0)), default=Value(1), output_field=IntegerField()),
    ).order_by('shift_priority', 'effective_shift_date', 'effective_shift', 'id')
