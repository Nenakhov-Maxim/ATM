from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from master.models import Tasks, Workplace
from django.contrib.auth.decorators import login_required, permission_required

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
