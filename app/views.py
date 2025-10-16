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
        print("📥 Получено от агента: изготовлен 1 профиль")

        # Ищем активную задачу на линии
        task = Tasks.objects.get(task_workplace_id=line_id, task_status_id=3)
        profile_amount_now = task.profile_amount_now
        Tasks.objects.filter(id=task.id).update(profile_amount_now=profile_amount_now + 1, last_update=datetime.datetime.now())
        

        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "invalid request"}, status=400)