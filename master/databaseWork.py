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
    self.now = self.tz.localize(datetime.datetime.now()) + timedelta(hours=5) 
  
  # Добавить новую задачу (мастер)  
  def add_new_task_data(self, user_name):
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
        task_history_id = self.history_id,
        task_profile_length = self.data['task_profile_length']
        )
      self.new_task_id = new_task.id
      return True
    except Exception as e:
      return f'Ошибка создания новой задачи: {e}'
  
  # Добавить новое значение в лог задачи
  def add_new_history_data(self,user_name, user_position, comment):
    # now = datetime.datetime.now()
    try:
      history_task = Task_history.objects.create(history_name={1:f"{self.now};Задача создана;{user_position} - {user_name}, комментарий: {comment}"})
      self.history_id = history_task.id      
      return True
    except Exception as e:
      return f'Ошибка создания истории: {e}'
  
  # Отправить задачу на выпонение рабочему (мастер) 
  def push_to_workers(self, user_name, user_position):
    # now = datetime.datetime.now()
    task = Tasks.objects.get(id=self.data['id_task'])
    history_task = Task_history.objects.get(id=task.task_history_id)    
    new_event = history_task.history_name
    max_key = max(new_event, key=new_event.get)
    new_event[int(max_key) + 1] = f'{self.now};Отправлена рабочему;{user_position} - {user_name}'
    history_check = [False, '']
    try:
      history_task.history_name = new_event
      history_task.save(update_fields=['history_name'])
      history_check = [True, '']            
    except Exception as e:
      history_check = [False, f'Ошибка изменения истории: {e}']    
    
    if history_check[0] ==  True:      
      try:
        task.task_status_id = 4
        task.save(update_fields=['task_status_id'])
        return  True
      except Exception as e:
        return f'Ошибка изменения статуса задачи: {e}'
    else:
      return history_check[1]
  
  # Приостановить выполнение задачи (мастер, рабочий)
  def paused_task(self, user_name, user_position, id_task):
    # now = datetime.datetime.now()
    task = Tasks.objects.get(id=id_task) 
    profile_amount = task.profile_amount_now          
    profile_index = 0
    my_str = task.worker_accepted_task
    arr_str = my_str.split(', ')
    worker_now = ''
    for value in arr_str:      
      start_i = value.find('(')
      end_i = value.find(')')
      try:
        int_data = int(value[start_i + 1:end_i])
        profile_index = profile_index + int_data           
      except Exception as e:
        int_data = int(profile_amount) - int(profile_index)        
        worker_now = task.worker_accepted_task + f'({int_data} - {self.now})'
        
    history_task = Task_history.objects.get(id=task.task_history_id)
    new_event = history_task.history_name
    max_key = max(new_event, key=new_event.get)
    new_event[int(max_key) + 1] = f"{self.now};Задача приостановлена;{user_position} - {user_name}, категория проблемы: {self.data['problem_type']}, комментарий: {self.data['problem_comments']}"
    history_check = [False, '']
    try:
      history_task.history_name = new_event
      history_task.save(update_fields=['history_name'])
      history_check = [True, '']            
    except Exception as e:
      history_check = [False, f'Ошибка изменения истории: {e}']    
    
    if history_check[0] ==  True:      
      try:
        task.worker_accepted_task = worker_now
        task.task_status_id = 6
        task.save(update_fields=['task_status_id', 'worker_accepted_task'])
        return  True
      except Exception as e:
        return f'Ошибка изменения статуса задачи: {e}'
    else:
      return history_check[1]
  
  # Удалить задачу (мастер) 
  def delete_task(self):
    try:
      task = Tasks.objects.get(id=self.data['id_task'])
      history_task = Task_history.objects.get(id=task.task_history_id)
      task.delete()
      history_task.delete()
    except Exception as e:
       return f'Ошибка удаления задачи: {e}'
  
  # Получить данные по задаче   
  def get_data_from_tasks(self):
    try:
      task = Tasks.objects.get(id=self.data['id_task'])     
      return task
    except Exception as e:
      return f'Ошибка удаления задачи: {e}'
  
  # Изменить задачу (Мастер)
  def edit_data_from_task(self, user_name, user_position, id_task):
    # now = datetime.datetime.now()  
    task = Tasks.objects.get(id=id_task)
    history_task = Task_history.objects.get(id=task.task_history_id)
    new_event = history_task.history_name
    max_key = max(new_event, key=new_event.get)
    new_event[int(max_key) + 1] = f'{self.now};Задача отредактирована;{user_position} - {user_name}'
    history_check = [False, '']
    try:
      history_task.history_name = new_event
      history_task.save(update_fields=['history_name'])
      history_check = [True, '']            
    except Exception as e:
      history_check = [False, f'Ошибка изменения истории: {e}']
    
    if history_check[0] ==  True:      
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
        # number - количество обновленных строк
        return  True
      except Exception as e:
        return f'Ошибка изменения статуса задачи: {e}'
    else:
      return history_check[1]
  
  # Старт выполнения работы рабочим  
  def start_working(self, id_task, user_name, user_position):
    # Получаем запись задачи, ее истории
    # now = datetime.datetime.now()  
    task = Tasks.objects.get(id=id_task)
    history_task = Task_history.objects.get(id=task.task_history_id)
    # генерируем новою запись в истории
    new_event = history_task.history_name
    max_key = max(new_event, key=new_event.get)
    new_event[int(max_key) + 1] = f'{self.now};Старт выполнения задачи;{user_position} - {user_name}, фактическое время начала - {self.now}'
    history_check = [False, '']
    # пробуем переписать историю
    try:
      history_task.history_name = new_event
      history_task.save(update_fields=['history_name'])
      history_check = [True, '']            
    except Exception as e:
      history_check = [False, f'Ошибка изменения истории: {e}']
    #  пробуем изменить статус и фактическое время начала задачи     
    if history_check[0] ==  True:
      worker_now = task.worker_accepted_task
      if len(worker_now) > 0:
          worker_now = worker_now + ', ' + user_name
      else:
          worker_now = user_name
      try:
        number = Tasks.objects.filter(id=id_task).update(        
        task_timedate_start_fact = self.now,
        task_status_id = 3,
        worker_accepted_task = worker_now     
      )
        # number - количество обновленных строк
        return  True
      except Exception as e:
        return f'Ошибка изменения статуса задачи: {e}'
    else:
      return history_check[1] 
    
  # Отмена выполнения работы рабочим  
  def deny_task(self, user_name, user_position, id_task):
    # now = datetime.datetime.now()
    task = Tasks.objects.get(id=id_task)
    history_task = Task_history.objects.get(id=task.task_history_id)
    new_event = history_task.history_name
    max_key = max(new_event, key=new_event.get)
    new_event[int(max_key) + 1] = f"{self.now};Выполнение задачи невозможно;{user_position} - {user_name}, категория проблемы: {self.data['problem_type']}, комментарий: {self.data['problem_comments']}"
    history_check = [False, '']
    try:
      history_task.history_name = new_event
      history_task.save(update_fields=['history_name'])
      history_check = [True, '']            
    except Exception as e:
      history_check = [False, f'Ошибка изменения истории: {e}']    
    
    if history_check[0] ==  True:      
      try:
        task.task_status_id = 5
        task.worker_accepted_task = ''
        task.save(update_fields=['task_status_id'])
        return  True
      except Exception as e:
        return f'Ошибка изменения статуса задачи: {e}'
    else:
      return history_check[1]
    
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
  def complete_task(self, id_task, user_name, user_position):
    # now = datetime.datetime.now()
    task = Tasks.objects.get(id=id_task)
    history_task = Task_history.objects.get(id=task.task_history_id)
    new_event = history_task.history_name
    max_key = max(new_event, key=new_event.get)
    new_event[int(max_key) + 1] = f"{self.now};Задача № {id_task} выполнена;{user_position} - {user_name}, фактическое время выполнения - {self.now}"
    history_check = [False, '']
    try:
      history_task.history_name = new_event
      history_task.save(update_fields=['history_name'])
      history_check = [True, '']            
    except Exception as e:
      history_check = [False, f'Ошибка изменения истории: {e}']    
    
    if history_check[0] ==  True:      
      try:
         # Кашапов Салават(55), Кашапов Салават(0), Кашапов Салават(55), Кашапов Салават(351)
        total_profile_amout = task.profile_amount_now
        profile_index = 0
        my_str = task.worker_accepted_task
        arr_str = my_str.split(', ')
        worker_now = ''
        for value in arr_str:
          start_i = value.find('(')
          end_i = value.find(')')
          try:
            int_data = value[start_i + 1:end_i]
            int_data = int(int_data.split(' - ')[0])
            profile_index = profile_index + int_data           
          except Exception as e:
            int_data = total_profile_amout - profile_index
            worker_now = task.worker_accepted_task + f'({int_data} - {self.now})'
            # print(f'{value[0:start_i]} изготовил {int_data} ед. профиля')
          
        task.worker_accepted_task = worker_now
        task.task_status_id = 2
        task.task_timedate_end_fact = self.now
        task.save(update_fields=['task_status_id', 'task_timedate_end_fact', 'worker_accepted_task'])
        return  True
      except Exception as e:
        return f'Ошибка завершения задачи: {e}'
      
    else:
      return history_check[1]
    
  # Старт переналадки
  def start_settingUp(self, id_task, user_name):
    # now = datetime.datetime.now()
    task = Tasks.objects.get(id=id_task)
    history_task = Task_history.objects.get(id=task.task_history_id)
    new_event = history_task.history_name
    max_key = max(new_event, key=new_event.get)
    new_event[int(max_key) + 1] = f"{self.now};Задача № {id_task};{user_name}, Старт наладки оборудования"
    history_check = [False, '']
    try:
      history_task.history_name = new_event
      history_task.save(update_fields=['history_name'])
      history_check = [True, '']            
    except Exception as e:
      history_check = [False, f'Ошибка изменения истории: {e}']    
    
    if history_check[0] ==  True:      
      try:
        task.task_status_id = 7
        task.task_time_settingUp = self.now
        task.save(update_fields=['task_status_id', 'task_time_settingUp'])
        return  f'Задача № {id_task}. Старт переналадки'
      except Exception as e:
        return f'Ошибка изменения статуса задачи: {e}'
    else:
      return history_check[1]
    
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
  def change_profile_amount(self, id_task, value):
    task = Tasks.objects.get(id=id_task)
    try:
      task.profile_amount_now = int(value)      
      task.save(update_fields=['profile_amount_now'])
      return True
    except Exception as e:
      print(f'Ошибка изменения текущего количества профиля в задаче: {e}') 
      return False 
 
 # Пересменка
  def shiftChange(self, id_task, profile_amount):
    task = Tasks.objects.get(id= id_task)       
    profile_index = 0
    my_str = task.worker_accepted_task
    arr_str = my_str.split(', ')
    worker_now = ''
    for value in arr_str:      
      start_i = value.find('(')
      end_i = value.find(')')
      try:
        int_data = int(value[start_i + 1:end_i])
        profile_index = profile_index + int_data           
      except Exception as e:
        int_data = int(profile_amount) - int(profile_index)        
        worker_now = task.worker_accepted_task + f'({int_data} - {self.now})'        
    history_task = Task_history.objects.get(id=task.task_history_id)
    new_event = history_task.history_name
    max_key = max(new_event, key=new_event.get)
    new_event[int(max_key) + 1] = f"{self.now};Для задачи № {id_task} выполняется пересменка; Фактическое время приостановки - {self.now}"
    history_check = [False, '']
    try:
      history_task.history_name = new_event
      history_task.save(update_fields=['history_name'])
      history_check = [True, '']            
    except Exception as e:
      history_check = [False, f'Ошибка изменения истории: {e}']    
    
    if history_check[0] ==  True:      
      try:
        task.worker_accepted_task = worker_now
        task.task_status_id = 8
        task.save(update_fields=['worker_accepted_task', 'task_status_id'])
        return True
      except Exception as e:
        print(f'Ошибка при выполнении пересменки: {e}') 
        return False
    
    
       
