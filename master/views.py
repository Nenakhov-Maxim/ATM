from django.shortcuts import render
from .models import HistoryEvent, OffsShtrips, Tasks
from .access import available_areas, available_workplaces, selected_area, task_area_query, accessible_task
from .forms import NewTaskForm, EditTaskForm, PauseTaskForm, ReportForm
from .databaseWork import DatabaseWork
from .shifts import production_shift_at
from .shift_selection import with_effective_shift
from datetime import date
from django.http import HttpResponse, JsonResponse, FileResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.db.models.deletion import ProtectedError
from django.db import transaction
from django.db.models import Prefetch, Q
from django.views.decorators.http import require_POST
from .profiling_invoice_report import create_profiling_invoice_report
from .completed_work_report import create_completed_work_report
from .report_periods import report_filename
import math, os
from datetime import datetime
import json


def request_param(request, key):
  if request.content_type and request.content_type.startswith('application/json'):
    try:
      data = json.loads(request.body)
      return data.get(key)
    except Exception:
      return None
  return request.POST.get(key)





@login_required
@permission_required(perm='master.view_tasks', raise_exception=True)
def master_home(request):
  area_id = selected_area(request.user, request.GET.get("area"))
  new_task_form = NewTaskForm(user=request.user)
  edit_task_form = EditTaskForm(user=request.user)
  new_paused_form = PauseTaskForm()
  report_form = ReportForm()
  tasks = Tasks.objects.filter(
    Q(task_is_vision=True) & 
    task_area_query(request.user, area_id)).select_related(
      'task_status',
      'task_workplace__production_area_id',
      'production_area',
      'task_profile_type',
      'task_coating_type',
    ).prefetch_related(
      Prefetch(
        'history_event_messages',
        queryset=HistoryEvent.objects.select_related('type_event', 'user').order_by('created_at', 'id'),
      ),
      Prefetch(
        'history_offs_shtrips',
        queryset=OffsShtrips.objects.select_related('type_value_id').order_by('created_at', 'id'),
      ),
    ).order_by('-id') 
    
  tasks_stat_all = tasks.count()
  tasks_stat_complited = Tasks.objects.filter(
    Q(task_status=2) & Q(task_is_vision=True) & 
    task_area_query(request.user, area_id)).count()
  selected_day = None
  selected_shift = None
  try:
    if request.GET.get('production_date'):
      selected_day = date.fromisoformat(request.GET['production_date'])
    if request.GET.get('shift'):
      selected_shift = int(request.GET['shift'])
      if selected_shift not in (1, 2, 3):
        raise ValueError
  except ValueError:
    return HttpResponse('Некорректная дата или смена', status=400)
  if selected_day or selected_shift:
    tasks = with_effective_shift(tasks)
    if selected_day:
      tasks = tasks.filter(effective_shift_date=selected_day)
    if selected_shift:
      tasks = tasks.filter(effective_shift=selected_shift)
  load_data = {'title': 'AT-Manager', "task_stat": f'{tasks_stat_all}/{tasks_stat_complited}'}
  if request.user.position_id_id == 1:
    user_prd = 'Мастер'
  else:
    user_prd = 'Рабочий'
  
  user_info = [request.user.first_name, request.user.last_name, user_prd]
  return render(request, 'master.html', {'load_data': load_data, 'new_task_form':new_task_form,
                                         'edit_task_form': edit_task_form, 'new_paused_form':new_paused_form,
                                         'tasks': tasks, 'report_form': report_form, 'user_info': user_info,
                                         'selected_day': selected_day, 'selected_shift': selected_shift,
                                         'available_areas': available_areas(request.user), 'selected_area_id': area_id,
                                         'workplace_areas': {str(w.pk): w.production_area_id_id for w in available_workplaces(request.user)}})

@login_required()
@permission_required(perm='master.change_tasks', raise_exception=True)
@require_POST
def start_task(request):
  id_task = request_param(request, 'id_task')
  if not id_task:
    return JsonResponse({'success': False, 'message': 'missing id_task'}, status=400)
  accessible_task(request.user, id_task)
  data_task = DatabaseWork({'id_task':id_task})
  task = data_task.push_to_workers(request.user)
  if task == True:
    return JsonResponse({'success': True, 'message': 'Статус задачи успешно обновлен'})
  else:
    return JsonResponse({'success': False, 'message': f'Ошибка обновления задачи: {task}'}, status=400)

# Приостановка выполнения задания 
@login_required 
@permission_required(perm='master.change_tasks', raise_exception=True)
def pause_task(request, id_task):
  accessible_task(request.user, id_task)
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
    order_number_array = request.POST.getlist('task_order_number')
    coating_type_array = request.POST.getlist('task_coating_type')
    variant_count = len(profile_length_array)
    if not variant_count or any(
      len(values) != variant_count
      for values in (profile_amount_array, order_number_array, coating_type_array)
    ):
      return HttpResponse('Ошибка: некорректно заполнены варианты длины продукции', status=400)

    common_data = request.POST.dict()
    task_forms = []

    for index, profile_length in enumerate(profile_length_array):
      task_data = common_data.copy()
      task_data.update({
        'task_profile_length': profile_length,
        'task_profile_amount': profile_amount_array[index],
        'task_order_number': order_number_array[index],
        'task_coating_type': coating_type_array[index],
      })

      new_task_form = NewTaskForm(task_data, user=request.user)
      if new_task_form.is_valid():
        task_forms.append(new_task_form)
      else:
        return HttpResponse(f'Ошибка заполнения формы: {new_task_form.errors}', status=400)

    try:
      with transaction.atomic():
        for new_task_form in task_forms:
          new_data_file = DatabaseWork(new_task_form.cleaned_data)
          new_task_file = new_data_file.add_new_task_data(request.user)
          if new_task_file is not True:
            raise RuntimeError(new_task_file)
          print(f'Добавление прошло успешно, id записи: {new_data_file.new_task_id}')
    except Exception as error:
      return HttpResponse(f'Ошибка: {error}', status=400)
    return redirect('/master', permanent=True)   

# Удаление задачи    
@login_required
@permission_required(perm='master.change_tasks', raise_exception=True)  
def delete_task(request):
  # POST only
  if request.method != 'POST':
    return JsonResponse({'success': False, 'message': 'Только POST-запрос'}, status=405)
  ids = request_param(request, 'id_tasks')
  if ids is not None:
    if not isinstance(ids, list) or not ids or any(
        isinstance(value, bool) or not str(value).isdigit() for value in ids):
      return JsonResponse({'message': 'Выберите задачи для удаления'}, status=400)
    ids = set(map(int, ids))
    try:
      with transaction.atomic():
        tasks = Tasks.objects.select_for_update(of=('self',)).filter(
          task_area_query(request.user),
          pk__in=ids, task_status_id=4,
        )
        if len(list(tasks)) != len(ids):
          return JsonResponse({'message': 'Можно удалить только ожидающие старта задачи своего участка'}, status=400)
        tasks.delete()
    except ProtectedError:
      return JsonResponse({'message': 'Задачи связаны с другими записями и не могут быть удалены'}, status=400)
    return JsonResponse({'success': True, 'message': 'Задачи удалены', 'count': len(ids)})
  accessible_task(request.user, request_param(request, 'id_task'))
  data_task = DatabaseWork({'id_task':request_param(request, 'id_task')})
  task = data_task.delete_task()
  if task == True:
    return JsonResponse({'success': True, 'message': 'Задача удалена'})
  else:
    return JsonResponse({'success': False, 'message': f'Ошибка удаления задачи: {task}'}, status=400) 

# Изменение задачи  
@login_required
@permission_required(perm='master.change_tasks', raise_exception=True)  
def edit_task(request):
  if request.method == 'GET':
      data = accessible_task(request.user, request.GET.get('id_task'))
      if not isinstance(data, Tasks):
        return JsonResponse({'error': 'Задание не найдено'}, status=404)
      shift_date, shift = data.task_shift_date, data.task_shift
      if shift_date is None and data.task_timedate_start:
        shift_date, shift = production_shift_at(data.task_timedate_start)
      return JsonResponse({'task_name': data.task_name, 'task_timedate_start':data.task_timedate_start,
                          'id_task': data.id, 'task_shift_date': shift_date, 'task_shift': shift,
                          'allow_stock': data.allow_stock,
                          'task_timedate_end': data.task_timedate_end, 'task_profile_type': data.task_profile_type_id, 
                          'task_workplace': data.task_workplace_id, 'task_area': data.task_workplace.production_area_id_id if data.task_workplace_id else data.production_area_id, 'task_profile_amount': data.task_profile_amount,
                          'task_profile_length': data.task_profile_length, 'task_comments': data.task_comments,
                          'task_order_number': data.task_order_number,
                          'task_profile_material': data.task_profile_material,
                          'task_coating_type': data.task_coating_type_id, 'task_coating_area': data.task_coating_area,
                          'task_coating_thickness': data.task_coating_thickness})
  elif request.method == 'POST':    
    accessible_task(request.user, request.POST.get('id_task'))
    edit_task_form = EditTaskForm(request.POST, user=request.user)    
    if edit_task_form.is_valid():      
      new_data_file = DatabaseWork(edit_task_form.cleaned_data)    
      new_task_file = new_data_file.edit_data_from_task(edit_task_form.cleaned_data['id_task'], request.user)
      if  new_task_file == True:
        return redirect('/master', permanent=True)
      else:
        return HttpResponse(f'Ошибка: {new_task_file}')
    return HttpResponse(f'Ошибка заполнения формы: {edit_task_form.errors}', status=400)
  else:
    return HttpResponse('Только GET или POST', status=405)
    
@login_required
@permission_required(perm='master.change_tasks', raise_exception=True)  
def hide_task(request):
  # POST only
  if request.method != 'POST':
    return JsonResponse({'success': False, 'message': 'Только POST-запрос'}, status=405)
  ids = request_param(request, 'id_tasks')
  if ids is not None:
    if not isinstance(ids, list) or not ids or any(
        isinstance(value, bool) or not str(value).isdigit() for value in ids):
      return JsonResponse({'message': 'Выберите задачи для скрытия'}, status=400)
    ids = set(map(int, ids))
    with transaction.atomic():
      tasks = Tasks.objects.select_for_update(of=('self',)).filter(
        task_area_query(request.user),
        pk__in=ids, task_status_id=2,
      )
      if len(list(tasks)) != len(ids):
        return JsonResponse({'message': 'Можно скрыть только завершённые задачи своего участка'}, status=400)
      tasks.update(task_is_vision=False)
    return JsonResponse({'success': True, 'message': 'Задачи скрыты', 'count': len(ids)})
  accessible_task(request.user, request_param(request, 'id_task'))
  data_task = DatabaseWork({'id_task':request_param(request, 'id_task')})
  task = data_task.hide_task()
  if task == True:
    return JsonResponse({'success': True, 'message': 'Задача скрыта'})
  else:
    return JsonResponse({'success': False, 'message': f'Ошибка скрытия задачи: {task}'}, status=400)


@login_required
@permission_required(perm='master.change_tasks', raise_exception=True)
@require_POST
def new_report(request):
  form = ReportForm(request.POST)
  if not form.is_valid():
    return JsonResponse({'message': 'Проверьте параметры отчёта.', 'errors': form.errors}, status=400)
  data = form.cleaned_data
  area_id = selected_area(request.user, request.POST.get('area'))
  filename = report_filename('Акт', data)
  answer = create_completed_work_report(data['periods'], request.user, filename, data['period_label'], area_id=area_id)
  return FileResponse(open(answer, 'rb'), as_attachment=True, filename=filename)


@login_required
@permission_required(perm='master.change_tasks', raise_exception=True)
@require_POST
def profiling_invoice_report(request):
  form = ReportForm(request.POST)
  if not form.is_valid():
    return JsonResponse({'message': 'Проверьте параметры отчёта.', 'errors': form.errors}, status=400)
  data = form.cleaned_data
  area_id = selected_area(request.user, request.POST.get('area'))
  filename = report_filename('Накладная', data)
  answer = create_profiling_invoice_report(
    data['date_start'], data['date_end'], request.user, output_filename=filename,
    periods=data['periods'], period_label=data['period_label'], area_id=area_id,
  )
  return FileResponse(open(answer, 'rb'), as_attachment=True, filename=filename)


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
