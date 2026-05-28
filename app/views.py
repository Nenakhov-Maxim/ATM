from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from master.models import HistoryProfileRecords, TaskProfileRecord, Tasks
from master.history_utils import infer_profile_record_user
from django.db import transaction
from django.db.models import F
from django.utils import timezone


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

            legacy_record = HistoryProfileRecords.objects.create(
                user=record_user,
                amount=1,
                profile_sum=task.profile_amount_now,
            )
            task.history_profile_records.add(legacy_record)
            TaskProfileRecord.objects.create(
                task=task,
                user=record_user,
                amount=1,
                profile_sum=task.profile_amount_now,
            )

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
