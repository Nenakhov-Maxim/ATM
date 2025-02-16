from django.db import models
from django.contrib.postgres.fields import HStoreField



class Access_app(models.Model):  
  access_name = models.CharField('Наименование', max_length=50)
  page_access = models.CharField('Страницы')
  
  def __str__(self):
    return self.access_name
  
class Positions(models.Model): 
  positions_name = models.CharField('Наименование', max_length=50)
  position_access = models.ForeignKey('Access_app', on_delete=models.CASCADE)
  
  def __str__(self):
    return self.positions_name  

class Task_status(models.Model):
  status_name = models.CharField('Наименование', max_length=100)
  
  def __str__(self):
    return self.status_name
  
class Profile_type(models.Model):
  profile_name = models.CharField('Наименование', max_length=100)
  
  def __str__(self):
    return self.profile_name
  
class Workplace(models.Model):
  workplace_name = models.CharField('Наименование рабочего места', max_length=250)
  type_of_equipment = models.CharField('Наименование оборудования', max_length=250)
  inv_number = models.IntegerField('Инвентарный номер оборудования')
  
  def __str__(self):
    return self.workplace_name
  
class Task_history(models.Model):    
  history_name = HStoreField()
  
  def __str__(self):
    return str(self.id) 

class MasterTypeProblem(models.Model):
  name_problem = models.CharField('Наименование типа проблемы', max_length=100)
  
  def __str__(self):
    return str(self.name_problem) 
  
  

class Tasks(models.Model):
  task_name = models.CharField('Наименование', max_length=250)
  task_timedate_start = models.DateTimeField('Дата и время начала', null=True, blank=True)
  task_timedate_end = models.DateTimeField('Дата и время окончания', null=True, blank=True)
  task_profile_type = models.ForeignKey('Profile_type', null=True, on_delete=models.SET_NULL)
  task_workplace = models.ForeignKey('Workplace', null=True, on_delete=models.SET_NULL)
  task_profile_amount = models.BigIntegerField('Количество')
  task_comments = models.TextField('Комментарий', blank=True)
  task_status = models.ForeignKey('Task_status', null=True, on_delete=models.SET_NULL)
  task_user_created = models.CharField('Кто создал задачу', max_length=250, default='Неизвестный пользователь')
  task_history = models.ForeignKey('Task_history',  on_delete=models.CASCADE)
  task_timedate_start_fact = models.DateTimeField('Фактическая дата и время начала', null=True, blank=True)
  task_timedate_end_fact = models.DateTimeField('Фактическая дата и время окончания', null=True, blank=True)
  task_is_vision = models.BooleanField('Видимость задачи', default=True)
  task_time_settingUp = models.DateTimeField('Фактическая дата и время начала наладки', null=True, blank=True)
  profile_amount_now = models.BigIntegerField('Количество профиля текущего', default=0)
  task_profile_length = models.FloatField('Длина профиля',  default=0)
  worker_accepted_task = models.TextField('ФИО рабочего', blank=True)
  
  def __str__(self):
    return self.task_name
  
  class Meta():
    verbose_name = 'Задачи'
    verbose_name_plural = 'Задачи'  