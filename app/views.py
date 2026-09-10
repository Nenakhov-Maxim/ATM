from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from master.models import HistoryProfileRecords, TaskProfileRecord, Tasks
from master.history_utils import infer_profile_record_user
from master.production import record_output
from django.db import transaction
from django.db.models import F
from django.utils import timezone


def _json_request_data(request):
    try:
        return json.loads(request.body or b"{}")
    except Exception:
        return None


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    value = str(value).strip().lower()
    if value in ("1", "true", "yes", "on", "enable", "enabled"):
        return True
    if value in ("0", "false", "no", "off", "disable", "disabled"):
        return False
    return None


def _agent_token_is_valid(request, data):
    expected_token = getattr(settings, "AUTOMATIC_VISION_API_TOKEN", "")
    if not expected_token:
        return True
    token = request.headers.get("X-ATM-Agent-Token") or data.get("token")
    return token == expected_token


@csrf_exempt
def arduino_data(request):
    if request.method != "POST":
        return JsonResponse({"error": "invalid request"}, status=400)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "invalid json"}, status=400)

    value = data.get('data')
    line_id = data.get('line_id')

    if value is None or line_id is None:
        return JsonResponse({"error": "missing fields"}, status=400)

    try:
        line_id = int(line_id)
    except (TypeError, ValueError):
        return JsonResponse({"error": "invalid line_id"}, status=400)

    # heartbeat / keepalive from Arduino (не считаем за профиль)
    try:
        if str(value) == '0':
            return JsonResponse({"status": "ok", "message": "heartbeat"})
    except Exception:
        pass

    if str(value) == 'start_ai':
        try:
            with transaction.atomic():
                task = (
                    Tasks.objects
                    .select_for_update()
                    .filter(task_workplace_id=line_id, task_status_id=3)
                    .order_by('-task_timedate_start_fact', '-id')
                    .first()
                )
                if task is None:
                    return JsonResponse({"status": "no_active_task"}, status=409)

                task.sensor_true = True
                task.save(update_fields=['sensor_true'])
                task.refresh_from_db(fields=['sensor_true'])
        except Exception as e:
            print(f"Ошибка при обновлении sensor_ai: {e}")
            return JsonResponse({"status": "error", "detail": str(e)}, status=500)
    elif str(value) == 'pause_ai':
        try:
            with transaction.atomic():
                task = (
                    Tasks.objects
                    .select_for_update()
                    .filter(task_workplace_id=line_id, task_status_id=3)
                    .order_by('-task_timedate_start_fact', '-id')
                    .first()
                )
                if task is None:
                    return JsonResponse({"status": "no_active_task"}, status=409)

                task.sensor_true = False
                task.save(update_fields=['sensor_true'])
                task.refresh_from_db(fields=['sensor_true'])
        except Exception as e:
            print(f"Ошибка при обновлении sensor_ai: {e}")
            return JsonResponse({"status": "error", "detail": str(e)}, status=500)

    # Только при явном сигнале '1' инкрементируем
    if str(value) != '1':
        return JsonResponse({"status": "ignored"})

    try:
        with transaction.atomic():
            task = (
                Tasks.objects
                .select_for_update()
                .filter(task_workplace_id=line_id, task_status_id=3)
                .order_by('-task_timedate_start_fact', '-id')
                .first()
            )
            if task is None:
                return JsonResponse({"status": "no_active_task"}, status=409)

            if not task.sensor_true:
                return JsonResponse({"status": "sensor_disabled"}, status=409)

            task.profile_amount_now = F('profile_amount_now') + 1
            task.last_update = timezone.now()
            task.save(update_fields=['profile_amount_now', 'last_update'])
            task.refresh_from_db(fields=['profile_amount_now'])

            record_user = infer_profile_record_user(task)

            record_output(task, 1, record_user, task.last_update)

            return JsonResponse({
                "status": "ok",
                "task_id": task.id,
                "profile_amount_now": task.profile_amount_now,
            })
    except Exception as e:
        print(f"Ошибка при обновлении профиля: {e}")
        return JsonResponse({"status": "error", "detail": str(e)}, status=500)
    


@login_required
@require_POST
def activate_sensor(request, task_id, bool_val):
    try:
        task = Tasks.objects.get(id=task_id)
    except Tasks.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Task not found"}, status=404)

    enabled = str(bool_val).lower() in ('1', 'true', 'yes', 'on')
    task.sensor_true = enabled
    task.save(update_fields=['sensor_true'])

    return JsonResponse({
        "status": "ok",
        "task_id": task_id,
        "sensor_true": task.sensor_true,
    })


@csrf_exempt
@require_POST
def automatic_vision_by_line(request):
    data = _json_request_data(request)
    if data is None:
        return JsonResponse({"status": "error", "message": "invalid json"}, status=400)

    if not _agent_token_is_valid(request, data):
        return JsonResponse({"status": "error", "message": "invalid token"}, status=403)

    line_id = data.get("line_id")
    try:
        line_id = int(line_id)
    except (TypeError, ValueError):
        return JsonResponse({"status": "error", "message": "invalid line_id"}, status=400)

    action = str(data.get("action", "")).strip().lower()
    enabled = _parse_bool(data.get("enabled"))

    with transaction.atomic():
        task = (
            Tasks.objects
            .select_for_update()
            .filter(task_workplace_id=line_id, task_status_id=3)
            .order_by("-task_timedate_start_fact", "-id")
            .first()
        )
        if task is None:
            return JsonResponse({"status": "no_active_task", "line_id": line_id}, status=409)

        old_value = task.sensor_true
        if action == "toggle":
            enabled = not old_value
        elif action in ("stop", "disable", "off"):
            enabled = False
        elif action in ("start", "enable", "on"):
            enabled = True

        if enabled is None:
            return JsonResponse({
                "status": "error",
                "message": "pass enabled=true/false or action=toggle|stop|start",
            }, status=400)

        task.sensor_true = enabled
        task.save(update_fields=["sensor_true"])

    return JsonResponse({
        "status": "ok",
        "line_id": line_id,
        "task_id": task.id,
        "sensor_true": task.sensor_true,
        "previous_sensor_true": old_value,
    })
