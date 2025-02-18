from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from master.models import Tasks

def get_home_page(request):  
  work_task_lib = {}
  flow_task_lib = {}
  koef_success_lib = {}
  tasks_in_work = Tasks.objects.all().filter(task_status_id__in=[3, 7]).order_by('task_status_id')
  tasks_in_flow = Tasks.objects.all().filter(task_status_id=4).order_by('task_timedate_start')[:5]
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
