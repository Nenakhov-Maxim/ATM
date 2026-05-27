from django.shortcuts import render
from master.models import *
from master.databaseWork import DatabaseWork
from django.http import HttpResponse, JsonResponse
from .forms import PauseTaskForm, DenyTaskForm
from django.db.models import Count, Prefetch, Q
import datetime
from datetime import timedelta
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from app.telegramAPI import TelegramBot
import json


def request_param(request, key):
  """Read parameter from POST form or JSON body"""
  if request.content_type and request.content_type.startswith('application/json'):
    try:
      data = json.loads(request.body)
      return data.get(key)
    except Exception:
      return None
  return request.POST.get(key)

# Стратовая страница
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True) 
def worker_home(request, filter='all'):
  new_paused_form = PauseTaskForm()
  new_deny_form = DenyTaskForm()  
  now = datetime.datetime.now()
  adr_lib = {'192.168.211.10': 1, '192.168.211.11': 2, '192.168.211.12': 3, '192.168.211.13': 4, '192.168.211.14': 5, '192.168.211.15': 6}
  if request.META['REMOTE_ADDR'] in adr_lib.keys():
    area_id = adr_lib[request.META['REMOTE_ADDR']]
    user_prd_ar = f'Производственная линия № {str(area_id)}'
  else:
    user_prd_ar = 'Неизвестная линия'
    area_id = 1 #99  
  tasks = Tasks.objects.filter(
    task_workplace=area_id,
    task_status_id__in=[3, 4, 7, 8]
  ).select_related(
    'task_status',
    'task_profile_type',
    'task_coating_type',
  ).prefetch_related(
    Prefetch(
      'history_offs_shtrips',
      queryset=OffsShtrips.objects.select_related('type_value_id').order_by('created_at', 'id'),
    ),
  ).order_by('-id')  
  task_stats = tasks.aggregate(
    task_to_start=Count('id', filter=Q(task_status_id=4)),
    task_start=Count('id', filter=Q(task_status_id=3)),
  )
  task_to_start = task_stats['task_to_start']
  task_start = task_stats['task_start']
  user_info = [request.user.first_name, request.user.last_name, request.user.position_id.position, user_prd_ar]
  if filter == 'now':
    tasks = tasks.filter(task_timedate_start__lte = now)
  elif filter == 'week':    
    tasks = tasks.filter(task_timedate_start__lte = now + datetime.timedelta(days=5))
  elif filter == 'month':    
    tasks = tasks.filter(task_timedate_start__lte = now + datetime.timedelta(days=30))
  
  return render(request, 'worker.html', {'filter': filter, 'tasks':tasks, 'task_to_start':task_to_start,
                                         'task_start':task_start, 'user_info':user_info, 'new_paused_form':new_paused_form,
                                         'new_deny_form':new_deny_form, 'line_id':area_id})

# Запуск задания в работу (POST only)
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True)
@require_POST
def start_working(request):
  # Получаем id задачи из POST
  id_task = request_param(request, 'id_task')
  if not id_task:
    return JsonResponse({'success': False, 'message': 'missing id_task'}, status=400)
  data_task = DatabaseWork({'id_task':id_task})
  result = data_task.start_working(id_task, request.user)
  if result == True:
    return JsonResponse({'success': True, 'message': 'Статус задачи успешно обновлен'})
  return JsonResponse({'success': False, 'message': result}, status=400)
  
# Изменение фильтра-меню(сегодня)
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True)   
def task_now(request):
  filter = 'now'
  return_value = worker_home(request, filter)
  
  return return_value

# Изменение фильтра-меню(неделя)
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True) 
def task_week(request):
  filter = 'week'
  return_value = worker_home(request, filter)
  
  return return_value

# Изменение фильтра-меню (месяц)
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True) 
def task_month(request):
  filter = 'month'
  return_value = worker_home(request, filter)
  
  return return_value

# Приостановка выполнения задания
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True) 
def pause_task(request):    
  if request.method == 'POST':
    adr_lib = {'192.168.211.10': 1, '192.168.211.11': 2, '192.168.211.12': 3, '192.168.211.13': 4, '192.168.211.14': 5, '192.168.211.15': 6}
    new_paused_form = PauseTaskForm(request.POST)
    if new_paused_form.is_valid():
      new_data_file = DatabaseWork(new_paused_form.cleaned_data)        
      new_task_file = new_data_file.paused_task(new_paused_form.cleaned_data['task_id'], request.user) 
      if  new_task_file == True:
        if new_paused_form.cleaned_data['problem_type'].id == 1:
          if request.META['REMOTE_ADDR'] in adr_lib.keys():
            area_id = adr_lib[request.META['REMOTE_ADDR']]
          else:
            area_id = 99
          comment = new_paused_form.cleaned_data['problem_comments']  
          TelegramBot().send_text(f'На линии {area_id} произошла неисправность.  Комментарий рабочего: "{comment}"')      
        return redirect('/worker', permanent=True)
      else:
        return HttpResponse(f'Ошибка: {new_task_file}')
  elif request.method == 'GET':    
    id_task_local = request.GET.get('id_task')        
    return HttpResponse(f'Данные отправлены на сервер, id записи: {id_task_local}') 
  else:
    new_task_form = PauseTaskForm()

# Отмена выполнения задания
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True)     
def deny_task(request):   
  if request.method == 'POST':
    adr_lib = {'192.168.211.10': 1, '192.168.211.11': 2, '192.168.211.12': 3, '192.168.211.13': 4, '192.168.211.14': 5, '192.168.211.15': 6}    
    new_deny_form = DenyTaskForm(request.POST)    
    if new_deny_form.is_valid():      
      new_data_file = DatabaseWork(new_deny_form.cleaned_data)         
      new_task_file = new_data_file.deny_task(new_deny_form.cleaned_data['task_id'], request.user)        
      if  new_task_file == True:
        if new_deny_form.cleaned_data['problem_type'].id == 1:
          if request.META['REMOTE_ADDR'] in adr_lib.keys():
            area_id = adr_lib[request.META['REMOTE_ADDR']]
          else:
            area_id = 99
          comment = new_deny_form.cleaned_data['problem_comments']  
          try:
            TelegramBot().send_text(f'На линии {area_id} произошла неисправность.  Комментарий рабочего: "{comment}"')
          except Exception as e:
            print(e)
        return redirect('/worker', permanent=True)
      else:        
        return HttpResponse(f'Ошибка: {new_task_file}')
  elif request.method == 'GET':
    id_task_local = request.GET.get('id_task')     
    return HttpResponse(f'Данные отправлены на сервер, id записи:{id_task_local}') 
  else:
    new_task_form = DenyTaskForm()

# Завершение задачи (POST only)
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True)
@require_POST
def complete_task(request):
  # Получаем id задачи
  id_task = request_param(request, 'id_task')
  if not id_task:
    return JsonResponse({'success': False, 'message': 'missing id_task'}, status=400)
  id_user = request.user.id
  data_task = DatabaseWork({'id_task':id_task})
  result = data_task.complete_task(id_task, request.user)
  if result != True:
    return JsonResponse({'success': False, 'message': result}, status=400)
  data_task.add_data_to_user_analytics(int(id_user), int(id_task))
  return JsonResponse({'success': True, 'message': 'Задача завершена'})
  
# Старт наладки/переналадки (POST only)
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True)
@require_POST
def start_settingUp(request):
  id_task = request_param(request, 'id_task')
  if not id_task:
    return JsonResponse({'success': False, 'message': 'missing id_task'}, status=400)
  data_task = DatabaseWork({'id_task':id_task})
  result = data_task.start_settingUp(id_task, request.user)
  if str(result).startswith('Ошибка'):
    return JsonResponse({'success': False, 'message': result}, status=400)
  return JsonResponse({'success': True, 'message': result})

# Изменение текущего количества профиля в БД (POST only)
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True)
@require_POST
def edit_profile_amount(request):
  task_id = request_param(request, 'id_task')
  value = request_param(request, 'value')
  if not task_id or value is None:
    return JsonResponse({'success': False, 'message':'missing parameters'}, status=400)
  data_task = DatabaseWork({'id_task':task_id})
  result = data_task.change_profile_amount(task_id, value, request.user)
  if result:
    return JsonResponse({'success': True, 'message':'ОК'})
  else:
    return JsonResponse({'success': False, 'message':'Error'}, status=400)
  
  # Пересменка (POST only)
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True)
@require_POST
def shiftChange(request):
  task_id = request_param(request, 'id_task')
  if not task_id:
    return JsonResponse({'success': False, 'message':'missing id_task'}, status=400)
  data_task = DatabaseWork({'id_task':task_id})
  result = data_task.shiftChange(task_id, request.user)
  if result:
    return JsonResponse({'success': True, 'message':'ОК'})
  return JsonResponse({'success': False, 'message':'Ошибка пересменки'}, status=400)

# Списание штрипса
@csrf_exempt
@require_http_methods(["POST"])
def shtripsOffs(request):
  try:
    data_json = json.loads(request.body)
    data = data_json.get('data')
    value = data['val_num']
    type_value = ShtripsValueType.objects.get(id=data['type'])
    task_id = data['task_id']
    task = Tasks.objects.get(id=task_id)
    task.history_offs_shtrips.create(value=value, type_value_id=type_value)
    last_history = OffsShtrips.objects.latest('id')
    
    date_value = last_history.created_at + timedelta(hours=5)
    return JsonResponse({
                'success': True, 
                'id': int(last_history.id),
                'value': float(last_history.value),
                'date_value': str(date_value),
                'type_value': str(last_history.type_value_id.type_offs_shtrips)
            })
  except Exception as e:
    print(e)
    return JsonResponse({
                'success': False, 
                'error': 'Ошибка на сервере'
            })
