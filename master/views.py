from django.shortcuts import render
from .models import Tasks, SteelTypeProfile
from .forms import NewTaskForm, EditTaskForm, PauseTaskForm, ReportForm
from .databaseWork import DatabaseWork
from django.http import HttpResponse, JsonResponse, FileResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from .report import create_excel_from_dict_list
import math, os
from datetime import timedelta, datetime
import json





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
  if request.user.position_id_id == 1:
    user_prd = 'Мастер'
  else:
    user_prd = 'Рабочий'
  
  user_info = [request.user.first_name, request.user.last_name, user_prd]
  return render(request, 'master.html', {'load_data': load_data, 'new_task_form':new_task_form,
                                         'edit_task_form': edit_task_form, 'new_paused_form':new_paused_form,
                                         'tasks': tasks, 'report_form': report_form, 'user_info': user_info})

@login_required()
@permission_required(perm='master.change_tasks', raise_exception=True)
def start_task(request):    
  if request.method == 'GET':
    data_task = DatabaseWork({'id_task':request.GET.get('id_task')})
    task = data_task.push_to_workers(request.user)     
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
      new_data_file = DatabaseWork(new_paused_form.cleaned_data)                   
      new_task_file = new_data_file.paused_task(id_task, request.user)        
      if  new_task_file == True:
        return redirect('/master', permanent=True)
      else:
        return HttpResponse(f'Ошибка: {new_task_file}')
   
# Добавление новой задачи
@login_required
@permission_required(perm='master.add_tasks', raise_exception=True)
def new_task(request):
  if request.method == 'POST':
    profile_length_array = request.POST.getlist('task_profile_length')
    profile_amount_array = request.POST.getlist('task_profile_amount')
    amount_date_period = len(profile_length_array)
    date_start = datetime.strptime(request.POST.get('task_timedate_start'), "%Y-%m-%dT%H:%M") 
    date_end = datetime.strptime(request.POST.get('task_timedate_end'), "%Y-%m-%dT%H:%M")
    total_hour = ((date_end - date_start).total_seconds()) / 3600
    time_for_sector = total_hour / amount_date_period
    start_position = date_start            
    for index, value in enumerate(profile_length_array):               
      decleaned_data = {}      
      for key in request.POST:
        if key == 'task_profile_length':
          decleaned_data['task_profile_length'] = value
        elif key == 'task_profile_amount':
          decleaned_data['task_profile_amount'] = profile_amount_array[index]
        elif key == 'task_timedate_start':
          decleaned_data['task_timedate_start'] = start_position
        elif key == 'task_timedate_end':
          decleaned_data['task_timedate_end'] = start_position + timedelta(hours=time_for_sector)
          start_position = start_position + timedelta(hours=time_for_sector)
        else:
          decleaned_data[key] = request.POST[key]
      new_task_form = NewTaskForm(decleaned_data)
      if new_task_form.is_valid():
        type_material_id = request.POST.get('task_type_material')
        user_name = f'{request.user.last_name} {request.user.first_name}'
        new_data_file = DatabaseWork(new_task_form.cleaned_data)       
        new_task_file = new_data_file.add_new_task_data(user_name, type_material_id, request.user)        
        if  new_task_file == True:
          print(f'Добавление прошло успешно, id записи: {new_data_file.new_task_id}')            
        else:
          return HttpResponse(f'Ошибка: {new_task_file}')
    return redirect('/master', permanent=True)   

# Получение списка материалов для поля "Материал" при создании заявки
@csrf_exempt
# @login_required
# @permission_required(perm='master.change_task', raise_exception=True)
@require_http_methods(["POST"])
def get_material(request):
  try:
    data = json.loads(request.body)
    profile_id = data.get('profile_id', '').strip()
    materials_list = SteelTypeProfile.objects.all().filter(type_profile_id=profile_id)
    material_name_list = {}
    for item in materials_list:
      material_name_list[item.type_steel.id] = item.type_steel.name
    
    return JsonResponse({
      'success': True,
      'data': material_name_list
    })
    
  except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Произошла ошибка: {str(e)}'
        })
  

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
                          'task_profile_length': data.task_profile_length, 'task_comments': data.task_comments})
  elif request.method == 'POST':    
    edit_task_form = EditTaskForm(request.POST)    
    if edit_task_form.is_valid():      
      new_data_file = DatabaseWork(edit_task_form.cleaned_data)    
      new_task_file = new_data_file.edit_data_from_task(id_task, request.user)        
      if  new_task_file == True:
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
      print(start_date)
      print(end_date)   
      tasks = Tasks.objects.all().filter(last_update__range=(start_date, end_date))
      print(tasks)
      dict_list = {}
      for task in tasks:
        id_task = task.id
        label_task = f'Задача ID № {id_task} от {task.created_at + timedelta(hours=5)}. Списаны штрипсы: '
        # Обрабатываем штрипсы
        shtrips_list_str = ""
        for shtrips in task.get_all_history_shtrips():
          if shtrips.type_value_id.id == 1:
            shtrips_list_str = shtrips_list_str + str(shtrips.value) + '; '
          else:
              # получаем материал у задачи
              material = task.task_profile_material
              # получаем тип профиля
              type_profile = task.task_profile_type
              # Находим запись в таблице соответствий, указывающую на кг в погонном метре
              value_kg_m = SteelTypeProfile.objects.get(type_profile=type_profile, type_steel=material)
              # Вес профиля умножаем на длину остатка и добавляем в общую строку
              value_to_add = round(value_kg_m.weight * shtrips.value, 2)
              shtrips_list_str = shtrips_list_str + str(shtrips.value) + "(п.м.)" + str(value_to_add) + "(кг.)" + "; "
        
        # Дописываем какие штрипсы были списаны по задаче
        label_task = label_task + shtrips_list_str    
        # Обрабатываем записи по каждому событию изготовления профиля
        # Объединяем по именю
        data_lib = {}
        all_records = task.history_profile_records.all()

        for record in all_records:
          if record.created_at >= start_date and record.created_at <= end_date:
            user = f'{record.user.last_name} {record.user.first_name}'
            profile_amount = record.amount
            if user in data_lib.keys():
              old_value = data_lib[user]
              data_lib[user] = old_value + profile_amount
            else:
              data_lib[user] = profile_amount
              
        dict_list[id_task] = {'label':label_task, 'data':[]} 
        
        # Наполняем данными
        for key in data_lib.keys():    
          new_row = [key, task.task_workplace_id, task.task_profile_type.profile_name,
                     data_lib[key] * task.task_profile_length, "8", '0', 'Да', '']
          dict_list[id_task]['data'].append(new_row)
        
      header_list = ['Ф.И.О', 'Номер линии', 'Марка изделия', 'Общее кол-во п/м', 'Отработанные часы', 'Ср. зд.', 'Хоз. работы', 'Подпись работника']
      answer = create_excel_from_dict_list(header_list, dict_list, f'Акт от {datetime.date(datetime.now())}.xlsx')
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