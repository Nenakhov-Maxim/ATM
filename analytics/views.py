from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from master.models import Tasks
from login.models import Workplace
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
      new_str = f'Задание №{task.id}, профиль "{task.task_profile_type}", требуется: {task.task_profile_amount} шт., текущее количество: {task.profile_amount_now} шт. ({task.task_status})'
      
      old_value.append(new_str) 
      work_task_lib[line_number] = old_value
    else:
      if task.task_status_id == 3:
        koef_success = round(task.profile_amount_now / task.task_profile_amount * 100, 2)
        koef_success_lib[line_number] = koef_success
      new_str = f'Задание №{task.id}, профиль "{task.task_profile_type}", требуется: {task.task_profile_amount} шт., текущее количество: {task.profile_amount_now} шт. ({task.task_status})'
      work_task_lib[line_number] = [new_str]
  
  for task in tasks_in_flow:
    old_value = []
    line_number = task.task_workplace_id
    if line_number in flow_task_lib.keys():
      old_value = flow_task_lib[line_number]
      new_str = f'Задание №{task.id}, профиль "{task.task_profile_type}", требуется: {task.task_profile_amount} шт., текущее количество: {task.profile_amount_now} шт.'
      old_value.append(new_str) 
      flow_task_lib[line_number] = old_value
    else:
      new_str = f'Задание №{task.id}, профиль "{task.task_profile_type}", требуется: {task.task_profile_amount} шт., текущее количество: {task.profile_amount_now} шт.'
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
      
    elif type_chart == 'hours_worked':
      data = update_hours_worked(int(filter))
      return JsonResponse({'answer':data})
    
    elif type_chart == 'effectiveness':
      data = update_effectiveness(int(filter))
      return JsonResponse({'answer':data})  
      
  else:
    return HttpResponse('Только GET-запрос')
  
# Обновление графика по изготовленному количеству изготовленного профиля рабочим
def update_current_profile(param):
  if param == 1:
    data = {}    
    tasks_in_work = Tasks.objects.all().filter(task_status_id__in=[3]).order_by('task_status_id')
    for task in tasks_in_work:
      profile_making_list = task.history_profile_records.all()
      for record in profile_making_list:
        user_key = f'{record.user.last_name} {record.user.first_name}'
        if user_key in data.keys():
          old_value = data[user_key]
          data[user_key] = old_value + record.amount
        else:
          data[user_key] = record.amount       
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
      if profile_type in data.keys():
        old_value = data[profile_type]
        data[profile_type] = old_value + profile_amount
      else:
        data[str(profile_type)] = profile_amount     
           
  return data

#Обновление графика производительность линии в час
def update_current_performance():
  date_end = datetime.datetime.now()  + datetime.timedelta(days=1) 
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
  date_end = datetime.datetime.now().date() + datetime.timedelta(days=1) 
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
  
  for task in tasks_in_work:
    profile_making_list = task.history_profile_records.first()
    if profile_making_list != None:
      timedate_start_fact = task.task_timedate_start_fact
      timedate_setting_up = task.task_time_settingUp
      user_making_setting_up = f'{profile_making_list.user.last_name} {profile_making_list.user.first_name}'
      seconds_in_day = 24 * 60 * 60
      dif_timedate_minute = round((timedate_setting_up - timedate_start_fact).seconds / 60, 2)
      
      if user_making_setting_up in data.keys():
        old_value = data[user_making_setting_up]
        data[user_making_setting_up] = (old_value + dif_timedate_minute) / 2
      else:
        data[user_making_setting_up] = dif_timedate_minute
  return data

#Обновление графика количества изготовленного профиля
def update_profile_amount(param):
  data = {}
  date_end = datetime.datetime.now().date() + datetime.timedelta(days=1)   
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
  
  for task in tasks_in_work:
    profile_making_list = task.history_profile_records.all()
    for record in profile_making_list:
      user_key = f'{record.user.last_name} {record.user.first_name}'
      if user_key in data.keys():
        old_value = data[user_key]
        data[user_key] = old_value + record.amount
      else:
        data[user_key] = record.amount   
  return data

def update_hours_worked(param):
  data = {}
  date_end = datetime.datetime.now().date() + datetime.timedelta(days=1)  
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
        
  tasks_in_work = Tasks.objects.all().filter(task_timedate_end_fact__isnull = False) & \
                  Tasks.objects.all().filter(task_timedate_end_fact__range = [date_start, date_end]) & \
                  Tasks.objects.all().filter(task_time_settingUp__isnull = False)

  for task in tasks_in_work:
    profile_making_list = task.history_profile_records.first()
    if profile_making_list != None:
      timedate_start_fact = task.task_timedate_start_fact
      timedate_setting_up = task.task_time_settingUp
      user_making_setting_up = f'{profile_making_list.user.last_name} {profile_making_list.user.first_name}'
      seconds_in_day = 24 * 60 * 60
      dif_timedate_minute = round((timedate_setting_up - timedate_start_fact).seconds / 60, 2)
      timedate_work_task = round((task.task_timedate_end_fact - task.task_timedate_start_fact).seconds / 60, 2)
      coef = round((timedate_work_task - dif_timedate_minute) / timedate_work_task, 2)
      if user_making_setting_up in data.keys():
        old_value = data[user_making_setting_up]
        data[user_making_setting_up] = (old_value + coef) / 2
      else:
        data[user_making_setting_up] = coef
  return data

# Обновление графика эффективности  
def update_effectiveness(param):
  data = {}
  date_end = datetime.datetime.now().date() + datetime.timedelta(days=1)  
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
        
  tasks_in_work = Tasks.objects.all().filter(task_timedate_end_fact__isnull = False) & \
                  Tasks.objects.all().filter(task_timedate_end_fact__range = [date_start, date_end])
                
  for task in tasks_in_work:
    timedate_start = task.task_timedate_start_fact
    profile_making_list = task.history_profile_records.all()
    for record in profile_making_list:
      user = f'{record.user.last_name} {record.user.first_name}'
      amount_profile = record.amount
      timedate_end = record.created_at
      time_to_work_hour = round((timedate_end - timedate_start).seconds / 60 / 60, 2)
      if time_to_work_hour != 0 and amount_profile != 0:
        effective = round(amount_profile / time_to_work_hour, 2)
        if user in data.keys():
          old_value = data[user]
          data[user] = (old_value + effective) / 2
        else:
          data[user] = effective 
      timedate_start = timedate_end
  return data