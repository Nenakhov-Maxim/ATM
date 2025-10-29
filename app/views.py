from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from master.models import Tasks
import datetime

@csrf_exempt
def arduino_data(request):
    if request.method == "POST":
        data = json.loads(request.body)
        
        value = data['data']
        line_id = data['line_id']
        # Ищем активную задачу на линии
        try:
            task = Tasks.objects.get(task_workplace_id=line_id, task_status_id=3)
            if task.sensor_true:
                profile_amount_now = task.profile_amount_now
                Tasks.objects.filter(id=task.id).update(profile_amount_now=profile_amount_now + 1, last_update=datetime.datetime.now())
                return JsonResponse({"status": "ok"})
            else:
                return JsonResponse({"status": "Пользователь отключил автоматическую фиксацию"}) 
        except Exception:
            print('Нет активной задачи')
            pass
    return JsonResponse({"error": "invalid request"}, status=400)

@csrf_exempt
def activate_sensor(request, task_id, bool_val):
    bool_val = bool_val
    if bool_val == 'true':
        bool_val = True
    else:
        bool_val = False
    task = Tasks.objects.filter(id=task_id).update(sensor_true=bool_val)
    return JsonResponse({"status": "ok", 'sensor_true': bool_val})