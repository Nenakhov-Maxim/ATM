from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


PRODUCTION_TIME_ZONE = ZoneInfo('Asia/Yekaterinburg')
SHIFT_CHOICES = (
    (1, '1 смена (08:00 - 17:00)'),
    (2, '2 смена (17:00 - 01:00)'),
    (3, '3 смена (01:00 - 08:00)'),
)


def production_shift_at(value):
    local = value.astimezone(PRODUCTION_TIME_ZONE)
    production_date = local.date()
    if local.hour < 8:
        production_date -= timedelta(days=1)
    shift = 1 if 8 <= local.hour < 17 else (2 if local.hour >= 17 or local.hour < 1 else 3)
    return production_date, shift


def current_production_date():
    return production_shift_at(datetime.now(timezone.utc))[0]


def shift_bounds(production_date, shift):
    # All three shifts belong to the production day beginning at 08:00.
    offsets = {1: (8, 17), 2: (17, 25), 3: (25, 32)}
    start_hour, end_hour = offsets[shift]
    midnight = datetime.combine(production_date, time(), tzinfo=PRODUCTION_TIME_ZONE)
    return tuple(
        (midnight + timedelta(hours=hour)).astimezone(timezone.utc)
        for hour in (start_hour, end_hour)
    )


def planned_shift_label(production_date, shift):
    if production_date is None or shift is None:
        return ''
    return f'{production_date:%d.%m.%Y}, {dict(SHIFT_CHOICES)[shift]}'
