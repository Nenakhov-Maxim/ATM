from django.shortcuts import render
from master.models import *
from master.databaseWork import DatabaseWork
from django.http import HttpResponse, JsonResponse
from .forms import PauseTaskForm, DenyTaskForm
import datetime
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import csrf_exempt

# Стратовая страница
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True) 
def worker_home(request, filter='all'):
  new_paused_form = PauseTaskForm()
  new_deny_form = DenyTaskForm()  
  now = datetime.datetime.now()
  if request.META['REMOTE_ADDR']=='192.168.211.10':
    user_prd_ar = 'Производственная линия № 1'
    area_id = 1
  else:
    user_prd_ar = 'Неизвестная линия'
    area_id = 0
  #Далее удалить при реальной эксплуатации
  area_id = 1 
  #area_id = request.user.production_area_id
  tasks = Tasks.objects.all().filter(task_workplace=area_id, task_status_id__in=[3, 4, 7, 8]).order_by('-id')
  task_to_start = tasks.filter(task_status_id=4).count
  task_start= tasks.filter(task_status_id=3).count
  user_info = [request.user.first_name, request.user.last_name, request.user.position_id, user_prd_ar]
  if filter == 'now':
    tasks = tasks.filter(task_timedate_start__lte = now)
  elif filter == 'week':    
    tasks = tasks.filter(task_timedate_start__lte = now + datetime.timedelta(days=5))
  elif filter == 'month':    
    tasks = tasks.filter(task_timedate_start__lte = now + datetime.timedelta(days=30))
  #print(request.META) 
  return render(request, 'worker.html', {'filter': filter, 'tasks':tasks, 'task_to_start':task_to_start,
                                         'task_start':task_start, 'user_info':user_info, 'new_paused_form':new_paused_form,
                                         'new_deny_form':new_deny_form, 'line_id':area_id})

# Запуск задания в работу
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True) 
def start_working(request):
  if request.method == 'GET':
    # Получаем id задачи
    id_task = request.GET.get('id_task')
    user_name = f'{request.user.last_name} {request.user.first_name}'
    user_position = request.user.position_id_id
    data_task = DatabaseWork({'id_task':id_task})
    result = data_task.start_working(id_task, user_name, user_position)
    
    return HttpResponse(result)
  
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
  global id_task
  if request.method == 'POST':
    new_paused_form = PauseTaskForm(request.POST)
    if new_paused_form.is_valid():
      user_name = f'{request.user.last_name} {request.user.first_name}'
      user_position =f'{request.user.position_id_id}'
      new_data_file = DatabaseWork(new_paused_form.cleaned_data)
      new_task_file = new_data_file.paused_task(user_name, user_position, id_task) 
      if  new_task_file == True:      
        return redirect('/worker', permanent=True)
      else:
        return HttpResponse(f'Ошибка: {new_task_file}')
  elif request.method == 'GET':
    id_task = request.GET.get('id_task')
    return HttpResponse(f'Данные отправлены на сервер, id записи: {id_task}') 
  else:
    new_task_form = PauseTaskForm()

# Отмена выполнения задания
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True)     
def deny_task(request):
  global id_task  
  if request.method == 'POST':    
    new_deny_form = DenyTaskForm(request.POST)    
    if new_deny_form.is_valid():      
      user_name = f'{request.user.last_name} {request.user.first_name}'
      user_position =f'{request.user.position_id_id}'
      new_data_file = DatabaseWork(new_deny_form.cleaned_data)                   
      new_task_file = new_data_file.deny_task(user_name, user_position, id_task)        
      if  new_task_file == True:
        
        return redirect('/worker', permanent=True)
      else:
        
        return HttpResponse(f'Ошибка: {new_task_file}')
  elif request.method == 'GET':
    id_task = request.GET.get('id_task') 
       
    return HttpResponse(f'Данные отправлены на сервер, id записи: {id_task}') 
  else:
    new_task_form = DenyTaskForm()

# Завершение задачи
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True)   
def complete_task(request):  
  if request.method == 'GET':    
    # Получаем id задачи
    id_task = request.GET.get('id_task')
    user_name = f'{request.user.last_name} {request.user.first_name}'
    user_position = request.user.position_id_id
    id_user = request.user.id
    data_task = DatabaseWork({'id_task':id_task})
    result = data_task.complete_task(id_task, user_name, user_position)
    data_task.add_data_to_user_analytics(int(id_user), int(id_task))
    return HttpResponse('') #result
  
# Старт наладки/переналадки
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True)
def start_settingUp(request):
  id_task = request.GET.get('id_task')
  user_name = f'{request.user.last_name} {request.user.first_name}'  
  data_task = DatabaseWork({'id_task':id_task})
  result = data_task.start_settingUp(id_task, user_name)  
  return JsonResponse({'answer':result})

# Изменение текущего количества профиля в БД
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True)
def edit_profile_amount(request):
  task_id = request.GET.get('id_task')
  value = request.GET.get('value')
  data_task = DatabaseWork({'id_task':task_id})
  result = data_task.change_profile_amount(task_id, value)
  if result:
    return JsonResponse({'answer':'ОК'})
  else:
    return JsonResponse({'answer':'Error'})
  
@login_required
@permission_required(perm='worker.change_workertypeproblem', raise_exception=True)
def shiftChange(request):  
  task_id = request.GET.get('id_task')
  profile_amount = request.GET.get('profile_amount')
  data_task = DatabaseWork({'id_task':task_id})
  result = data_task.shiftChange(task_id, profile_amount)
  return JsonResponse({'answer':'ОК'})
