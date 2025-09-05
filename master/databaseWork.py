from .models import *
from worker.models import *
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
  def add_new_task_data(self, user_name, material, user):
    try:            
      new_task = Tasks.objects.create(
        task_name = self.data['task_name'],
        task_timedate_start = self.data['task_timedate_start'],
        task_timedate_end = self.data['task_timedate_end'],
        task_profile_type_id = self.data['task_profile_type'].id,
        task_workplace_id = self.data['task_workplace'].id,
        task_profile_amount = self.data['task_profile_amount'],
        task_comments = self.data['task_comments'],
        task_status_id = 1,
        task_user_created = user_name,
        task_profile_length = self.data['task_profile_length'],
        task_profile_material = SteelType.objects.get(id=material),
        )
      
      new_task.history_event_messages.create(user=user, type_event=TypeEvent.objects.get(id=1), message=new_task.task_comments)
      return True
    except Exception as e:
      print(e)
      return f'Ошибка создания новой задачи: {e}'
  
  def push_to_workers(self, user):
    task = Tasks.objects.get(id=self.data['id_task'])
    task.history_event_messages.create(user=user, type_event=TypeEvent.objects.get(id=2), message=f"Задача отправлена на '{task.task_workplace.workplace_name}' для выполнения")
    task.task_status_id = 4
    task.save(update_fields=['task_status_id'])
    
  def paused_task(self, id_task, user):
    task = Tasks.objects.get(id=id_task) 
    task.history_event_messages.create(user=user, type_event=TypeEvent.objects.get(id=5), message=f"Выполнение задачи приостановлено. Категория проблемы: {self.data['problem_type']}, комментарий: {self.data['problem_comments']}")        
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
    task.history_event_messages.create(user=user, type_event=TypeEvent.objects.get(id=9), message=f"Задача изменена пользователем {user.last_name} {user.first_name}")
    try:
      number = Tasks.objects.filter(id=id_task).update(
      task_name = self.data['task_name'],
      task_timedate_start = self.data['task_timedate_start'],
      task_timedate_end = self.data['task_timedate_end'],
      task_profile_type_id = self.data['task_profile_type'].id,
      task_workplace_id = self.data['task_workplace'].id,
      task_profile_amount = self.data['task_profile_amount'],
      task_comments = self.data['task_comments'],
      task_timedate_start_fact = None     
    )
      return  True
    except Exception as e:
      return f'Ошибка изменения статуса задачи: {e}'
  
  # Старт выполнения работы рабочим  
  def start_working(self, id_task, user):
    task = Tasks.objects.get(id=id_task)
    task.history_event_messages.create(user=user, type_event=TypeEvent.objects.get(id=3),
                                       message=f"Задача принята рабочим {user.last_name} {user.first_name}. Старт изготовления продукции.")
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
    task.history_event_messages.create(user=user, type_event=TypeEvent.objects.get(id=4),
                                       message=f"Задача отклонена рабочим {user.last_name} {user.first_name}. Категория проблемы: {self.data['problem_type']} Сообщение от рабочего: {self.data['problem_comments']}")      
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
    task.history_event_messages.create(user=user, type_event=TypeEvent.objects.get(id=8),
                                       message=f"Рабочий {user.last_name} {user.first_name}' закончил изготовление. Фактически изготовлено: {task.profile_amount_now} ед.")     
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
    task.history_event_messages.create(user=user, type_event=TypeEvent.objects.get(id=6),
                                       message=f"Рабочий {user.last_name} {user.first_name}' приступил к выполнению пусконалодчных работ.")    
    try:
      task.task_status_id = 7
      task.task_time_settingUp = self.now
      task.save(update_fields=['task_status_id', 'task_time_settingUp'])
      return  f'Задача № {id_task}. Старт переналадки'
    except Exception as e:
      return f'Ошибка изменения статуса задачи: {e}'
    
  # Изменяем данные для пользовательской аналитики   
  def add_data_to_user_analytics(self, user_id, id_task): 
    string_date_key = f'{self.now.month}.{self.now.year}'
    task = Tasks.objects.get(id=id_task)
    date_start_settingUp =task.task_time_settingUp 
    date_start_work = task.task_timedate_start_fact.replace(tzinfo=None)
    date_end_work = task.task_timedate_end_fact
    if date_start_settingUp == None:
      date_start_settingUp = date_start_work.replace(tzinfo=None)
    else:
      date_start_settingUp = date_start_settingUp.replace(tzinfo=None)
    if date_end_work == None:
      date_end_work = self.now.replace(tzinfo=None)
    else:
      date_end_work = date_end_work .replace(tzinfo=None)
    time_settingUp = round((date_start_work - date_start_settingUp).seconds/60/60, 2)    
    profile_amount = task.task_profile_amount
    work_time = round((date_end_work - date_start_work).seconds/60/60, 2) 
    analytics_item = Users_analytics.objects.all().filter(userId_id=user_id)
    #Если записи найдены то проверям текущий месяц
    #Одновременно обновляем значения для наладки и количества изготовленного профиля (не вижу возможности, чтобы при наличие записи в переналадке, что-то отсутствовало в количестве изготовленного профиля)
    if len(analytics_item)  > 0 :
      for value in analytics_item:
        #Если строка с текущим месяцем найдена то забираем от туда строку с данными и сверяем ID задачи
        if string_date_key in value.settingUp.keys():        
          sum_settingUp = value.settingUp[string_date_key].split(';')
          sum_profile_amount = value.profile_amount[string_date_key].split(';')
          sum_woktime = value.profile_amount[string_date_key].split(';')
          new_string_value_settingUp = ''
          new_string_value_profile_amount = ''
          new_string_value_wokrtime = ''
          check_search_id = False
          # Собираем заного строку, если нужный ID задачи не найден то строка остается без изменений и добавлется новое значение ID задачи
          for item_sup in sum_settingUp:
            if len(item_sup)>1:            
              task_id = item_sup.split(':')[0]
              old_time_settingUp = item_sup.split(':')[1]
              # Если же ID задачи найден то мы обновлем нужную запись, обнавлем переменную check_search_id  (флаг, что мы нашли запись) и собираем дальше строку, заканчивая цикл
              if str(id_task)==task_id:
                # Существует задача с таким же ID в переналадке             
                new_string_value_settingUp = new_string_value_settingUp + f'{task_id}:{time_settingUp};'               
              else:
                new_string_value_settingUp = new_string_value_settingUp + item_sup + ';'
          # Здесь тоже самое но по количеству изготовленного профиля    
          for item_pa in sum_profile_amount:            
            if len(item_pa)>1:                            
              task_id = item_pa.split(':')[0]
              old_time_settingUp = item_pa.split(':')[1]
              # Если же ID задачи найден то мы обновлем нужную запись, обнавлем переменную check_search_id  (флаг, что мы нашли запись) и собираем дальше строку, заканчивая цикл
              if str(id_task)==task_id:
                # Существует задача с таким же ID в количестве изготовленного профиля              
                new_string_value_profile_amount = new_string_value_profile_amount + f'{task_id}:{profile_amount};'            
              else:
                new_string_value_profile_amount = new_string_value_profile_amount + item_pa + ';'
           # Здесь тоже самое но по количеству полезного рабочего времени   
          for item_wt in sum_woktime:            
            if len(item_wt)>1:                            
              task_id = item_wt.split(':')[0]
              old_time_settingUp = item_wt.split(':')[1]
              # Если же ID задачи найден то мы обновлем нужную запись, обнавлем переменную check_search_id  (флаг, что мы нашли запись) и собираем дальше строку, заканчивая цикл
              if str(id_task)==task_id:
                # Существует задача с таким же ID в количестве изготовленного профиля              
                new_string_value_wokrtime = new_string_value_wokrtime + f'{task_id}:{work_time};'
                # Запись в строке обновлена
                check_search_id =  True
              else:
                new_string_value_wokrtime = new_string_value_wokrtime + item_wt + ';'
          # Так как нужная запись была найдена, то нет необходимости добавлять новую запись просто обновляем данные в таблице
          if check_search_id:
            new_dic_settingUp = {string_date_key:new_string_value_settingUp}
            new_dic_profile_amount = {string_date_key:new_string_value_profile_amount}
            new_dic_worktime = {string_date_key:new_string_value_wokrtime}
            analytics_item = Users_analytics.objects.all().filter(userId_id=user_id).update(
              settingUp=new_dic_settingUp,
              profile_amount=new_dic_profile_amount,
              work_time=new_dic_worktime
            )
          # Добавляем новое запись в БД, если предыдущее условие не сработало
          else:
              # Задачи с таким же ID не существует.  Добавляем новое зеачение  
              new_dic_settingUp = {string_date_key:f'{new_string_value_settingUp}{id_task}:{time_settingUp};'}
              new_dic_profile_amount = {string_date_key:f'{new_string_value_profile_amount}{id_task}:{profile_amount};'}
              new_dic_worktime = {string_date_key:f'{new_string_value_wokrtime}{id_task}:{work_time};'}
              analytics_item = Users_analytics.objects.all().filter(userId_id=user_id).update(
              settingUp=new_dic_settingUp,
              profile_amount=new_dic_profile_amount,
              work_time=new_dic_worktime
            )
    else:
      # Пользователь не найден
      new_task_time_settingUp = f'{id_task}:{time_settingUp};'
      new_task_profile_amount = f'{id_task}:{profile_amount};'
      new_task_woktime = f'{id_task}:{work_time};'
      Users_analytics.objects.create(userId_id=user_id, settingUp={string_date_key:new_task_time_settingUp},
                                     profile_amount={string_date_key:new_task_profile_amount},
                                     work_time ={string_date_key:new_task_woktime})   
 
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
        task.history_profile_records.create(user=user, amount=diff, profile_sum=int(value))
      else:
        task.history_profile_records.create(user=user, amount=int(value), profile_sum=int(value))  
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
