from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from master.models import Tasks, Workplace
from login.models import User
from django.contrib.auth.decorators import login_required, permission_required
import datetime

@login_required()
@permission_required(perm='master.change_tasks', raise_exception=True)
def get_home_page(request):  
  work_task_lib = {}
  flow_task_lib = {}
  koef_success_lib = {}
  tasks_in_work = Tasks.objects.all().filter(task_status_id__in=[3, 7]).order_by('task_status_id')
  tasks_in_flow = Tasks.objects.all().filter(task_status_id=4).order_by('task_timedate_start')[:5]
  workplace_lib = Workplace.objects.all()
  for workplace in workplace_lib:
    work_task_lib[workplace.id] = []
  for task in tasks_in_work:
    old_value = []
    line_number = task.task_workplace_id    
    if line_number in work_task_lib.keys():
      old_value = work_task_lib[line_number]
      new_str = f'Здание №{task.id}, профиль "{task.task_profile_type}", требуется: {task.task_profile_amount} шт., текущее количество: {task.profile_amount_now} шт. ({task.task_status})'
      
      old_value.append(new_str) 
      work_task_lib[line_number] = old_value
    else:
      if task.task_status_id == 3:
        koef_success = round(task.profile_amount_now / task.task_profile_amount * 100, 2)
        koef_success_lib[line_number] = koef_success
      new_str = f'Здание №{task.id}, профиль "{task.task_profile_type}", требуется: {task.task_profile_amount} шт., текущее количество: {task.profile_amount_now} шт. ({task.task_status})'
      work_task_lib[line_number] = [new_str]
  
  for task in tasks_in_flow:
    old_value = []
    line_number = task.task_workplace_id
    if line_number in flow_task_lib.keys():
      old_value = flow_task_lib[line_number]
      new_str = f'Здание №{task.id}, профиль "{task.task_profile_type}", требуется: {task.task_profile_amount} шт., текущее количество: {task.profile_amount_now} шт.'
      old_value.append(new_str) 
      flow_task_lib[line_number] = old_value
    else:
      new_str = f'Здание №{task.id}, профиль "{task.task_profile_type}", требуется: {task.task_profile_amount} шт., текущее количество: {task.profile_amount_now} шт.'
      flow_task_lib[line_number] = [new_str]

  return render(request, 'analitycs.html', {'work_task_lib': work_task_lib, 'flow_task_lib': flow_task_lib, 'koef_success_lib': koef_success_lib})

# Обновление графиков, общая функция
@login_required()
@permission_required(perm='master.change_tasks', raise_exception=True)
def update_chart(request, type_chart, filter):       
  if request.method == 'GET':
    if type_chart == 'current_profile':
      data = update_current_profile(filter)
      return JsonResponse({'answer':data})
  
    elif type_chart == 'current_performance':
      data = update_current_performance()
      return JsonResponse({'answer':data})
    
    elif type_chart == 'setup_speed':
      data = update_setup_speed(int(filter))
      return JsonResponse({'answer':data})
    
    elif type_chart == 'profile_amount':
      data = update_profile_amount(int(filter))
      return JsonResponse({'answer':data})  
      
  else:
    return HttpResponse('Только GET-запрос')
  
# Обновление графика по изготовленному количеству изготовленного профиля рабочим
def update_current_profile(param):
  if param == 1:
    data = {}    
    tasks_in_work = Tasks.objects.all().filter(task_status_id__in=[3]).order_by('task_status_id')
    for task in tasks_in_work:
      profile_amount = task.profile_amount_now
      workers = task.worker_accepted_task
      names_worker_list = workers.split(', ')
      
      for worker in names_worker_list:          
        start_i = worker.find('(')
        end_i = worker.find(')')      
        try:
          int_data = worker[start_i + 1:end_i]
          amount = int(int_data.split(' - ')[0])
          worker_name = worker[0:start_i]
          if worker_name in data.keys():
            old_value = data[worker_name]
            data[worker_name] = old_value + amount
          else:
            data[worker_name] = amount
        except Exception as e:
          worker_name = worker
          amount = profile_amount
          if worker_name in data.keys():
            old_value = data[worker_name]
            data[worker_name] = old_value + amount
          else:
            data[worker_name] = amount      
  if param == 3:
    data = {}    
    tasks_in_work = Tasks.objects.all().filter(task_status_id__in=[3]).order_by('task_status_id')
    for task in tasks_in_work:
      profile_amount = task.profile_amount_now
      workplace = str(task.task_workplace_id) + ' линия'        
      if workplace in data.keys():
        old_value = data[workplace]
        data[workplace] = old_value + profile_amount
      else:
        data[workplace] = profile_amount
  
  if param == 2:
    data = {}    
    tasks_in_work = Tasks.objects.all().filter(task_status_id__in=[3]).order_by('task_status_id')
    for task in tasks_in_work:
      profile_amount = task.profile_amount_now
      profile_type = task.task_profile_type 
      print(profile_type)       
      if profile_type in data.keys():
        old_value = data[profile_type]
        data[profile_type] = old_value + profile_amount
      else:
        data[str(profile_type)] = profile_amount     
           
  return data

#Обновление графика производительность линии в час
def update_current_performance():
  date_end = datetime.datetime.now()
  date_start = date_end - datetime.timedelta(weeks=4)
  data = {}    
  tasks_in_work = Tasks.objects.all().filter(task_timedate_end_fact__isnull = False) & Tasks.objects.all().filter(task_timedate_end_fact__range = [date_start, date_end])
  workplace_lib = Workplace.objects.all()
  for workplace in workplace_lib:
    data[workplace.id] = []
  for task in tasks_in_work:
    old_value = []
    time_to_work = task.task_timedate_end_fact - task.task_timedate_start_fact
    tasks_in_work_day = time_to_work.days   
    tasks_in_work_min = round((time_to_work.seconds / 60) + (tasks_in_work_day * 24 * 60), 2)
    if task.profile_amount_now != 0: 
      if task.task_workplace_id in data.keys():
        old_value = data[task.task_workplace_id]
        old_value.append((task.profile_amount_now / tasks_in_work_min) * 60)
        data[task.task_workplace_id] = old_value
      else:
        data[task.task_workplace_id] = [(task.profile_amount_now / tasks_in_work_min) * 60]    
  return data

#Обновление графика переналадки оборудования
def update_setup_speed(param):  
  data = {}
  date_end = datetime.datetime.now()  
  if param == 1:
    date_start = date_end - datetime.timedelta(days=1)
  elif param == 2:
    date_start = date_end - datetime.timedelta(days=7)
  elif param == 3:
    date_start = date_end - datetime.timedelta(weeks=4) 
  elif param == 4:
    date_start = date_end - datetime.timedelta(weeks=24)
  elif param == 5:
    date_start = date_end - datetime.timedelta(weeks=48)
  else: 
    date_start = date_end - datetime.timedelta(weeks=4800) 
        
  tasks_in_work = Tasks.objects.all().filter(task_time_settingUp__isnull = False) & Tasks.objects.all().filter(task_time_settingUp__range = [date_start, date_end])
  workers_summary = User.objects.all().filter(position_id_id = 2)
  
  for worker in workers_summary:    
    if worker.position_id_id == 2:
      worker_name = f'{worker.last_name} {worker.first_name}'
      data[worker_name] = []
  
  for task in tasks_in_work:
    date_start_sup = task.task_timedate_start_fact
    if date_start_sup ==  None:
      date_start_sup = datetime.datetime.now()  
    date_end_sup = task.task_time_settingUp          
    time_to_work = date_start_sup.replace(tzinfo=None) - date_end_sup.replace(tzinfo=None)  
    tasks_in_work_day = time_to_work.days   
    tasks_in_work_min = round((time_to_work.seconds / 60) + (tasks_in_work_day * 24 * 60), 2)   
    name_how_accept_task = (task.worker_accepted_task.split(', ')[0]).split('(')[0]
    if name_how_accept_task in data.keys():
      old_value = data[name_how_accept_task]
      old_value.append(tasks_in_work_min)
      data[name_how_accept_task] = old_value
    else:
      if 'Неизвестный пользователь' in data.keys():
        old_value = data['Неизвестный пользователь']
        old_value.append(tasks_in_work_min)
        data['Неизвестный пользователь'] = old_value
      else:
        data['Неизвестный пользователь'] = [tasks_in_work_min]         
  return data

#Обновление графика количества изготовленного профиля
def update_profile_amount(param):
  data = {}
  date_end = datetime.datetime.now()  
  if param == 1:
    date_start = date_end - datetime.timedelta(days=1)
  elif param == 2:
    date_start = date_end - datetime.timedelta(days=7)
  elif param == 3:
    date_start = date_end - datetime.timedelta(weeks=4) 
  elif param == 4:
    date_start = date_end - datetime.timedelta(weeks=24)
  elif param == 5:
    date_start = date_end - datetime.timedelta(weeks=48)
  else: 
    date_start = date_end - datetime.timedelta(weeks=4800) 
        
  tasks_in_work = Tasks.objects.all().filter(task_timedate_end_fact__isnull = False) & Tasks.objects.all().filter(task_timedate_end_fact__range = [date_start, date_end])
  workers_summary = User.objects.all().filter(position_id_id = 2)
  
  for worker in workers_summary:    
    if worker.position_id_id == 2:
      worker_name = f'{worker.last_name} {worker.first_name}'
      data[worker_name] = []
  
  for task in tasks_in_work:    
    array_workers_sum_inf = task.worker_accepted_task.split(', ')    
    for worker_sum_inf in array_workers_sum_inf:
      if worker_sum_inf.find('(') != -1 & worker_sum_inf.find(')') != -1:
        pos1 = worker_sum_inf.find('(')
        pos2 = worker_sum_inf.find(')')
        name_worker = worker_sum_inf[0:pos1]
        amount_profile = int(worker_sum_inf[pos1 + 1:pos2].split(' - ')[0])        
        if name_worker in data.keys():
          old_value = data[name_worker]
          old_value.append(amount_profile)
          data[name_worker] = old_value
        else:
          data['Неизвестный пользователь'] = [amount_profile]
      else:
        if worker_sum_inf != "":
          if worker_sum_inf in data.keys():
            old_value = data[worker_sum_inf]
            old_value.append(task.profile_amount_now)
            data[worker_sum_inf] = old_value
          else:
            data['Неизвестный пользователь'] = [int(task.profile_amount_now)]
        else:
          if 'Неизвестный пользователь' in data.keys():
            old_value = data['Неизвестный пользователь']
            old_value.append(task.profile_amount_now)
            data['Неизвестный пользователь'] = old_value
          else:
            data['Неизвестный пользователь'] = [int(task.profile_amount_now)]       
  
  return data