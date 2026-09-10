from .models import *
from worker.models import *
from .shifts import planned_shift_label
import datetime
from datetime import timezone, timedelta
import pytz

class DatabaseWork:
  def __init__ (self, data):
    self.data = data
    self.history_id = -1
    self.new_task_id = -1
    self.tz = pytz.timezone('UTC')
    self.now = self.tz.localize(datetime.datetime.now())
  
  # Добавить новую задачу (мастер)  
  def add_new_task_data(self, user):
    try:            
      user_name = f'{user.last_name} {user.first_name}'.strip() or user.username
      new_task = Tasks.objects.create(
        task_name = self.data['task_name'],
        task_timedate_start = self.data['task_timedate_start'],
        task_timedate_end = self.data['task_timedate_end'],
        task_shift_date = self.data['task_shift_date'],
        task_shift = self.data['task_shift'],
        task_profile_type_id = self.data['task_profile_type'].id,
        task_workplace_id = self.data['task_workplace'].id,
        task_profile_amount = self.data['task_profile_amount'],
        task_comments = self.data['task_comments'],
        task_status_id = 1,
        task_user_created = user_name,
        task_user_created_by = user,
        task_profile_length = self.data['task_profile_length'],
        task_order_number = self.data.get('task_order_number', ''),
        task_profile_material = self.data.get('task_profile_material'),
        task_coating_type = self.data.get('task_coating_type'),
        task_coating_area = self.data.get('task_coating_area'),
        task_coating_thickness = self.data.get('task_coating_thickness'),
        )
      
      # legacy M2M history (backwards-compatible)
      history_message = (
        f"Заказ № {new_task.task_order_number}. Плановая смена: {new_task.planned_shift_label}. "
        f"{new_task.task_comments or ''}"
      ).strip()
      new_history = new_task.history_event_messages.create(user=user, type_event=TypeEvent.objects.get(id=1), message=history_message)
      # normalized event
      try:
        TaskEvent.objects.create(task=new_task, user=user, type_event=TypeEvent.objects.get(id=1), message=history_message)
      except Exception:
        pass
      return True
    except Exception as e:
      print(e)
      return f'Ошибка создания новой задачи: {e}'
  
  def push_to_workers(self, user):
    try:
      task = Tasks.objects.get(id=self.data['id_task'])
      task.history_event_messages.create(user=user, type_event=TypeEvent.objects.get(id=2), message=f"Задача отправлена на '{task.task_workplace.workplace_name}' для выполнения")
      try:
        TaskEvent.objects.create(task=task, user=user, type_event=TypeEvent.objects.get(id=2), message=f"Задача отправлена на '{task.task_workplace.workplace_name}' для выполнения")
      except Exception:
        pass
      task.task_status_id = 4
      task.save(update_fields=['task_status_id'])
      return True
    except Exception as e:
      return f'Ошибка изменения статуса задачи: {e}'
    
  def paused_task(self, id_task, user):
    task = Tasks.objects.get(id=id_task) 
    new_history = task.history_event_messages.create(user=user, type_event=TypeEvent.objects.get(id=5), message=f"Выполнение задачи приостановлено. Категория проблемы: {self.data['problem_type']}, комментарий: {self.data['problem_comments']}")        
    try:
      TaskEvent.objects.create(task=task, user=user, type_event=TypeEvent.objects.get(id=5), message=f"Выполнение задачи приостановлено. Категория проблемы: {self.data['problem_type']}, комментарий: {self.data['problem_comments']}")
    except Exception:
      pass
    try:
      task.task_status_id = 6
      task.save(update_fields=['task_status_id'])
      return  True
    except Exception as e:
      return f'Ошибка изменения статуса задачи: {e}'
  
  # Удалить задачу (мастер) 
  def delete_task(self):
    try:
      task = Tasks.objects.get(id=self.data['id_task'])
      task.delete()
      return True
    except Exception as e:
       return f'Ошибка удаления задачи: {e}'
  
  # Получить данные по задаче   
  def get_data_from_tasks(self):
    try:
      task = Tasks.objects.get(id=self.data['id_task'])     
      return task
    except Exception as e:
      return f'Ошибка получения данных по задаче: {e}'
  
  # Изменить задачу (Мастер)
  def edit_data_from_task(self, id_task, user): 
    task = Tasks.objects.get(id=id_task)
    history_message = (
      f"Задача изменена пользователем {user.last_name} {user.first_name}. "
      f"Заказ № {self.data.get('task_order_number', '')}. "
      f"Плановая смена: {task.planned_shift_label or 'не указана'} -> "
      f"{planned_shift_label(self.data['task_shift_date'], self.data['task_shift'])}"
    )
    new_history = task.history_event_messages.create(user=user, type_event=TypeEvent.objects.get(id=9), message=history_message)
    try:
      TaskEvent.objects.create(task=task, user=user, type_event=TypeEvent.objects.get(id=9), message=history_message)
    except Exception:
      pass
    try:
      number = Tasks.objects.filter(id=id_task).update(
      task_name = self.data['task_name'],
      task_timedate_start = self.data['task_timedate_start'],
      task_timedate_end = self.data['task_timedate_end'],
      task_shift_date = self.data['task_shift_date'],
      task_shift = self.data['task_shift'],
      task_profile_type_id = self.data['task_profile_type'].id,
      task_workplace_id = self.data['task_workplace'].id,
      task_profile_amount = self.data['task_profile_amount'],
      task_profile_length = self.data['task_profile_length'],
      task_order_number = self.data.get('task_order_number', ''),
      task_profile_material = self.data.get('task_profile_material'),
      task_coating_type = self.data.get('task_coating_type'),
      task_coating_area = self.data.get('task_coating_area'),
      task_coating_thickness = self.data.get('task_coating_thickness'),
      task_comments = self.data['task_comments'],
    )
      return  True
    except Exception as e:
      return f'Ошибка изменения статуса задачи: {e}'
  
  # Старт выполнения работы рабочим  
  def start_working(self, id_task, user):
    task = Tasks.objects.get(id=id_task)
    new_history = task.history_event_messages.create(user=user, type_event=TypeEvent.objects.get(id=3),
                                       message=f"Задача принята рабочим {user.last_name} {user.first_name}. Старт изготовления продукции.")
    try:
      TaskEvent.objects.create(task=task, user=user, type_event=TypeEvent.objects.get(id=3), message=f"Задача принята рабочим {user.last_name} {user.first_name}. Старт изготовления продукции.")
    except Exception:
      pass
    try:
      number = Tasks.objects.filter(id=id_task).update(        
      task_timedate_start_fact = self.now,
      task_status_id = 3,     
    )
      return  True
    except Exception as e:
      return f'Ошибка изменения статуса задачи: {e}'
    
  # Отмена выполнения работы рабочим  
  def deny_task(self, id_task, user):
    task = Tasks.objects.get(id=id_task)
    new_history = task.history_event_messages.create(user=user, type_event=TypeEvent.objects.get(id=4),
                                       message=f"Задача отклонена рабочим {user.last_name} {user.first_name}. Категория проблемы: {self.data['problem_type']} Сообщение от рабочего: {self.data['problem_comments']}")      
    try:
      TaskEvent.objects.create(task=task, user=user, type_event=TypeEvent.objects.get(id=4), message=f"Задача отклонена рабочим {user.last_name} {user.first_name}. Категория проблемы: {self.data['problem_type']} Сообщение от рабочего: {self.data['problem_comments']}")
    except Exception:
      pass
    try:
      task.task_status_id = 5
      task.save(update_fields=['task_status_id'])
      return  True
    except Exception as e:
      return f'Ошибка изменения статуса задачи: {e}'
    
  # Скрыть задачу (мастер)
  def hide_task(self):
    task = Tasks.objects.get(id=self.data['id_task'])
    try:
        task.task_is_vision = False
        task.save(update_fields=['task_is_vision'])
        return  True
    except Exception as e:
        return f'Ошибка изменения статуса задачи: {e}'
      
  # Завершение задачи
  def complete_task(self, id_task, user):
    task = Tasks.objects.get(id=id_task)
    new_history = task.history_event_messages.create(user=user, type_event=TypeEvent.objects.get(id=8),
                                       message=f"Рабочий {user.last_name} {user.first_name}' закончил изготовление. Фактически изготовлено: {task.profile_amount_now} ед.")     
    try:
      TaskEvent.objects.create(task=task, user=user, type_event=TypeEvent.objects.get(id=8), message=f"Рабочий {user.last_name} {user.first_name}' закончил изготовление. Фактически изготовлено: {task.profile_amount_now} ед.")
    except Exception:
      pass
    try:
      task.task_status_id = 2
      task.task_timedate_end_fact = self.now
      task.save(update_fields=['task_status_id', 'task_timedate_end_fact']) #'worker_accepted_task'
      return  True
    except Exception as e:
      return f'Ошибка завершения задачи: {e}'
    
  # Старт переналадки
  def start_settingUp(self, id_task, user):
    task = Tasks.objects.get(id=id_task)
    new_history = task.history_event_messages.create(user=user, type_event=TypeEvent.objects.get(id=6),
                                       message=f"Рабочий {user.last_name} {user.first_name}' приступил к выполнению пусконалодчных работ.")    
    try:
      TaskEvent.objects.create(task=task, user=user, type_event=TypeEvent.objects.get(id=6), message=f"Рабочий {user.last_name} {user.first_name}' приступил к выполнению пусконалодчных работ.")
    except Exception:
      pass
    try:
      task.task_status_id = 7
      task.task_time_settingUp = self.now
      task.save(update_fields=['task_status_id', 'task_time_settingUp'])
      return  f'Задача № {id_task}. Старт переналадки'
    except Exception as e:
      return f'Ошибка изменения статуса задачи: {e}'
    
  # Изменяем данные для пользовательской аналитики   
  def add_data_to_user_analytics(self, user_id, id_task): 
    # Normalized analytics: create or update WorkerAnalyticsRecord per (user, task, month, year)
    task = Tasks.objects.get(id=id_task)
    date_start_settingUp = task.task_time_settingUp
    date_start_work = task.task_timedate_start_fact.replace(tzinfo=None)
    date_end_work = task.task_timedate_end_fact
    if date_start_settingUp is None:
      date_start_settingUp = date_start_work.replace(tzinfo=None)
    else:
      date_start_settingUp = date_start_settingUp.replace(tzinfo=None)
    if date_end_work is None:
      date_end_work = self.now.replace(tzinfo=None)
    else:
      date_end_work = date_end_work.replace(tzinfo=None)
    time_settingUp = round((date_start_work - date_start_settingUp).seconds/60/60, 2)
    profile_amount = task.task_profile_amount
    work_time = round((date_end_work - date_start_work).seconds/60/60, 2)

    month = self.now.month
    year = self.now.year
    try:
      record, created = WorkerAnalyticsRecord.objects.get_or_create(
        user_id=user_id,
        task_id=id_task,
        month=month,
        year=year,
        defaults={
          'setting_up_hours': time_settingUp,
          'profile_amount': profile_amount,
          'work_time_hours': work_time,
        }
      )
      if not created:
        # update existing record (overwrite with latest summary values)
        record.setting_up_hours = time_settingUp
        record.profile_amount = profile_amount
        record.work_time_hours = work_time
        record.save(update_fields=['setting_up_hours', 'profile_amount', 'work_time_hours'])
    except Exception as e:
      print(f'Ошибка сохранения аналитики: {e}')
 
  # Изменение профиля
  def change_profile_amount(self, id_task, value, user):
    task = Tasks.objects.get(id=id_task)
    try:
      last_row_records = task.history_profile_records.latest()
    except Exception as e:
      last_row_records= None  
    try:
      if last_row_records:
        diff = int(value) - last_row_records.profile_sum
        new_rec = task.history_profile_records.create(user=user, amount=diff, profile_sum=int(value))
      else:
        new_rec = task.history_profile_records.create(user=user, amount=int(value), profile_sum=int(value))  
      try:
        TaskProfileRecord.objects.create(task=task, user=user, amount=new_rec.amount, profile_sum=new_rec.profile_sum)
      except Exception:
        pass
      task.profile_amount_now = int(value)
      task.last_update = self.now  
      task.save(update_fields=['profile_amount_now', 'last_update'])
      return True
    except Exception as e:
      print(f'Ошибка изменения текущего количества профиля в задаче: {e}') 
      return False 
 
 # Пересменка
  def shiftChange(self, id_task, user):
    task = Tasks.objects.get(id= id_task)       
    task.history_event_messages.create(user=user, type_event=TypeEvent.objects.get(id=7),
                                       message=f"Рабочий {user.last_name} {user.first_name} приступил к пересменке. Текущее количество изготовленной продукции: {task.profile_amount_now} ед.")
    try:
      task.task_status_id = 8
      task.save(update_fields=['task_status_id'])
      return True
    except Exception as e:
      print(f'Ошибка при выполнении пересменки: {e}') 
      return False
