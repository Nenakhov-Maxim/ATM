UNKNOWN_PROFILE_RECORD_USER = 'Неизвестный пользователь'


def user_display_name(user):
    if user is None:
        return UNKNOWN_PROFILE_RECORD_USER

    name = f'{user.last_name or ""} {user.first_name or ""}'.strip()
    return name or getattr(user, 'username', '') or UNKNOWN_PROFILE_RECORD_USER


def profile_record_user_display_name(record, task=None):
    user = getattr(record, 'user', None)
    if user is not None:
        return user_display_name(user)

    if task is not None:
        worker_name = (getattr(task, 'worker_accepted_task', '') or '').strip()
        if worker_name:
            return worker_name

    return UNKNOWN_PROFILE_RECORD_USER


def infer_profile_record_user(task):
    event = (
        task.events
        .exclude(user__isnull=True)
        .select_related('user')
        .filter(type_event_id=3)
        .order_by('-created_at', '-id')
        .first()
    )
    if event is not None:
        return event.user

    event = (
        task.history_event_messages
        .exclude(user__isnull=True)
        .select_related('user')
        .filter(type_event_id=3)
        .order_by('-created_at', '-id')
        .first()
    )
    if event is not None:
        return event.user

    record = (
        task.history_profile_records
        .exclude(user__isnull=True)
        .select_related('user')
        .order_by('-created_at', '-id')
        .first()
    )
    if record is not None:
        return record.user

    record = (
        task.profile_records
        .exclude(user__isnull=True)
        .select_related('user')
        .order_by('-created_at', '-id')
        .first()
    )
    if record is not None:
        return record.user

    return None
