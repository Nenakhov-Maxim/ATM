from django.shortcuts import render
from .models import Tasks
from .forms import NewTaskForm, EditTaskForm, PauseTaskForm, ReportForm
from .databaseWork import DatabaseWork
from django.http import HttpResponse, JsonResponse, FileResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from .report import create_excel_from_dict_list
import math, datetime, os





@login_required
@permission_required(perm='master.view_tasks', raise_exception=True)
def master_home(request):
  new_task_form = NewTaskForm()
  edit_task_form = EditTaskForm()
  new_paused_form = PauseTaskForm()
  report_form = ReportForm()
  tasks = Tasks.objects.all().filter(task_is_vision=True).order_by('-id')    
  tasks_stat_all = Tasks.objects.all().count()
  tasks_stat_complited = Tasks.objects.filter(task_status=2).count()  
  load_data = {'title': 'AT-Manager', "task_stat": f'{tasks_stat_all}/{tasks_stat_complited}'}
  # print(request.META)
  
  return render(request, 'master.html', {'load_data': load_data, 'new_task_form':new_task_form,
                                         'edit_task_form': edit_task_form, 'new_paused_form':new_paused_form,
                                         'tasks': tasks, 'report_form': report_form})

@login_required()
@permission_required(perm='master.change_tasks', raise_exception=True)
def start_task(request):    
  if request.method == 'GET':
    data_task = DatabaseWork({'id_task':request.GET.get('id_task')})
    user_name = f'{request.user.last_name} {request.user.first_name}'
    user_position =f'{request.user.position}'
    task = data_task.push_to_workers(user_name, user_position)     
    if task == True:      
      return HttpResponse('Статус задачи успешно обновлен')
    else:
      return HttpResponse(f'Ошибка обновления задачи: {task}')
  else:
    return HttpResponse('Только GET-запрос')

# Приостановка выполнения задания 
@login_required 
@permission_required(perm='master.change_tasks', raise_exception=True)
def pause_task(request, id_task):   
  if request.method == 'POST':    
    new_paused_form = PauseTaskForm(request.POST)    
    if new_paused_form.is_valid():      
      user_name = f'{request.user.last_name} {request.user.first_name}'
      user_position =f'{request.user.position}'
      new_data_file = DatabaseWork(new_paused_form.cleaned_data)                   
      new_task_file = new_data_file.paused_task(user_name, user_position, id_task)        
      if  new_task_file == True:
        # print(f'Добавление прошло успешно, id записи: {new_data_file.new_task_id}')
        return redirect('/master', permanent=True)
      else:
        return HttpResponse(f'Ошибка: {new_task_file}')
   
# Добавление новой задачи
@login_required
@permission_required(perm='master.add_tasks', raise_exception=True)
def new_task(request):
  if request.method == 'POST':    
    new_task_form = NewTaskForm(request.POST)    
    if new_task_form.is_valid():      
      user_name = f'{request.user.last_name} {request.user.first_name}'
      user_position =f'{request.user.position}'
      new_data_file = DatabaseWork(new_task_form.cleaned_data)
      new_history_file = new_data_file.add_new_history_data(user_name, user_position, new_task_form.cleaned_data['task_comments'])            
      if new_history_file == True:        
        new_task_file = new_data_file.add_new_task_data(user_name)        
        if  new_task_file == True:
          # print(f'Добавление прошло успешно, id записи: {new_data_file.new_task_id}')
          return redirect('/master', permanent=True)
        else:
          return HttpResponse(f'Ошибка: {new_task_file}')
      else:        
        return HttpResponse(f'Ошибка: {new_history_file}')   

# Удаление задачи    
@login_required
@permission_required(perm='master.change_tasks', raise_exception=True)  
def delete_task(request):
  if request.method == 'GET':
    data_task = DatabaseWork({'id_task':request.GET.get('id_task')})
    task = data_task.delete_task()     
    if task == True:      
      return HttpResponse('Задача удалена')
    else:
      return HttpResponse(f'Ошибка удаления задачи: {task}') 

# Изменение задачи  
@login_required
@permission_required(perm='master.change_tasks', raise_exception=True)  
def edit_task(request):
  global id_task  
  if request.method == 'GET':
      id_task = request.GET.get('id_task')
      data_task = DatabaseWork({'id_task':request.GET.get('id_task')})
      data = data_task.get_data_from_tasks()      
      return JsonResponse({'task_name': data.task_name, 'task_timedate_start':data.task_timedate_start,
                          'task_timedate_end': data.task_timedate_end, 'task_profile_type': data.task_profile_type_id, 
                          'task_workplace': data.task_workplace_id, 'task_profile_amount': data.task_profile_amount,
                          'task_comments': data.task_comments})
  elif request.method == 'POST':    
    edit_task_form = EditTaskForm(request.POST)    
    if edit_task_form.is_valid():      
      user_name = f'{request.user.last_name} {request.user.first_name}'
      user_position =f'{request.user.position}'
      new_data_file = DatabaseWork(edit_task_form.cleaned_data)
      #new_history_file = new_data_file.add_new_history_data(user_name, user_position)       
      new_task_file = new_data_file.edit_data_from_task(user_name, user_position, id_task)        
      if  new_task_file == True:
        # print(f'Добавление прошло успешно, id записи: {new_data_file.new_task_id}')
        return redirect('/master', permanent=True)
      else:
        return HttpResponse(f'Ошибка: {new_task_file}')
      
  else:
    new_task_form = EditTaskForm() 
    
@login_required
@permission_required(perm='master.change_tasks', raise_exception=True)  
def hide_task(request):
  if request.method == 'GET':
    data_task = DatabaseWork({'id_task':request.GET.get('id_task')})
    task = data_task.hide_task()     
    if task == True:      
      return HttpResponse('Задача скрыта')
    else:
      return HttpResponse(f'Ошибка скрытия задачи: {task}')
  else:
    return HttpResponse('Только GET-запрос')


@login_required
@permission_required(perm='master.change_tasks', raise_exception=True)
def new_report(request):
  if request.method == 'POST':
    report_form = ReportForm(request.POST)
    if report_form.is_valid():
      data = report_form.cleaned_data
      start_date = data['date_start']
      end_date = data['date_end']
      tasks = Tasks.objects.all().filter(task_timedate_end_fact__range=(start_date, end_date))
      dict_list = []
      for task in tasks:
        profile_index = 0
        my_str = task.worker_accepted_task
        arr_str = my_str.split(', ')
        for value in arr_str:
          start_i = value.find('(')
          end_i = value.find(')')         
          int_data = int(value[start_i + 1:end_i])
          profile_index = profile_index + int_data
          total_length = round(float(task.task_profile_length) * int(int_data), 2) 
          total_time = dates_to_time(task.task_timedate_start_fact, task.task_timedate_end_fact)         
          new_row = {'Ф.И.О': value[0:start_i], 'Номер линии': task.task_workplace_id, 'Марка изделия': task.task_profile_type.profile_name, 'Общее кол-во п/м': total_length,
                                                        'Отработанные часы':total_time, 'Ср. ед.':'0', 'Хоз. работы':'Да', 'Подпись работника':''}
          dict_list.append(new_row)
        
      answer = create_excel_from_dict_list(dict_list, f'Акт от {datetime.date.today()}.xlsx')
      link = f'/app/{answer}'
      link = link.replace('\\', '/')      
      return FileResponse(open(os.path.join(answer), "rb"))
    else:
      return redirect('/master', permanent=True)
  
  else:
    return HttpResponse('Только GET-запрос')  


def dates_to_time(date1, date2):
  hourse_string = '0'
  minutes_string = '0'
  seconds_string = '0'
  result_time = date2 - date1  
  sum_difference = math.modf(result_time.total_seconds() / 60 / 60)
  hours = int(sum_difference[1])
  if abs(hours)  < 10:
    if hours < 0:
      hourse_string = f'-0{abs(hours)}'
    else:
      hourse_string = f'0{hours}'
  else:
      hourse_string = f'{hours}'  
  
     
       
  minutes_sum = math.modf(sum_difference[0] * 60)
  minutes = abs(int(minutes_sum[1]))
  if minutes  < 10:
    minutes_string = f'0{minutes}'
  else:
    minutes_string = f'{minutes}'    
  seconds = abs(int(minutes_sum[0] * 60) )   
  if seconds  < 10:
    seconds_string = f'0{seconds}'
  else:
    seconds_string = f'{seconds}'     
    
  return f'{hourse_string}:{minutes_string}:{seconds_string}'