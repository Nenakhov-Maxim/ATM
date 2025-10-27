import django
from django.db import models
from django.contrib.postgres.fields import HStoreField
from datetime import datetime, timezone
from login.models import User, Workplace


class AccessApp(models.Model):
    """Модель для управления доступом к приложению"""
    access_name = models.CharField('Наименование', max_length=50)
    page_access = models.CharField('Страницы', max_length=500)
    
    def __str__(self):
        return self.access_name
    
    class Meta:
        verbose_name = 'Доступ к приложению'
        verbose_name_plural = 'Доступы к приложению'


class Positions(models.Model):
    """Модель должностей пользователей"""
    positions_name = models.CharField('Наименование', max_length=50)
    position_access = models.ForeignKey('AccessApp', on_delete=models.CASCADE, verbose_name='Доступ')
    
    def __str__(self):
        return self.positions_name
    
    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'


class TaskStatus(models.Model):
    """Модель статусов задач"""
    status_name = models.CharField('Наименование', max_length=100)
    
    def __str__(self):
        return self.status_name
    
    class Meta:
        verbose_name = 'Статус задачи'
        verbose_name_plural = 'Статусы задач'
        
class TypeEvent(models.Model):
    """Типы событий для отображения"""
    type_name = models.CharField('Тип события', max_length=100)
    color = models.CharField('Цвет в формате #456456', max_length=100)

class HistoryEvent(models.Model):
    """Модель истории событий и сообщений""" 
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    type_event = models.ForeignKey('TypeEvent', null=True, on_delete=models.SET_NULL)
    message = models.CharField('Сообщение', max_length=500)
    created_at = models.DateTimeField('Фактическая дата и время списания', default=django.utils.timezone.now)

class ShtripsValueType(models.Model):
    """Типы значений для для списания штрипса"""
    type_offs_shtrips = models.CharField('Тип списания (кг или метры)')

class OffsShtrips(models.Model):
    """Модель истории списания штрипсов"""
    value = models.FloatField('Значение')
    type_value_id = models.ForeignKey('ShtripsValueType', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField('Фактическая дата и время списания', default=django.utils.timezone.now)
    
    def __str__(self):
        return str(self.value)
    
    class Meta:
        verbose_name = 'История списания'
        verbose_name_plural = 'Истории списаний'

class SteelType(models.Model):
    name = models.CharField('Наименование', blank=True, default='')
    width_steel = models.FloatField('Толщина стали', blank=True)
    
class SteelTypeProfile(models.Model):
     """Соответствие типа и толщины стали от типа профиля"""
     type_profile = models.ForeignKey('ProfileType', null=True, on_delete=models.SET_NULL, verbose_name='Тип профиля')
     type_steel = models.ForeignKey('SteelType', null=True, on_delete=models.SET_NULL, verbose_name='Тип стали')
     weight = models.FloatField('вес профиля (кг/пог.м)', blank=True)


class ProfileType(models.Model):
    """Модель типов профилей"""
    profile_name = models.CharField('Наименование', max_length=100)
    association_name_shtrips = models.CharField('Тип штрипса', blank=True, default='', null=True, max_length=100)
    is_accepted_video = models.BooleanField('Доступно для видео?', default=False, null=True)
    yolo_model_name = models.CharField('Название модели нейросети', blank=True, default='')
    paint_consumption = models.FloatField('Расход краски', blank=True, default=0.0)
    quantity_per_package = models.IntegerField('Количество в упаковке', blank=True, default=0)
    
    def __str__(self):
        return self.profile_name
    
    class Meta:
        verbose_name = 'Тип профиля'
        verbose_name_plural = 'Типы профилей'

class TaskHistory(models.Model):
    """Модель истории задач"""
    history_name = HStoreField(verbose_name='История')
    
    def __str__(self):
        return f'История задачи #{self.id}'
    
    class Meta:
        verbose_name = 'История задачи'
        verbose_name_plural = 'История задач'


class MasterTypeProblem(models.Model):
    """Модель типов проблем для мастера"""
    name_problem = models.CharField('Наименование типа проблемы', max_length=100)
    
    def __str__(self):
        return self.name_problem
    
    class Meta:
        verbose_name = 'Тип проблемы'
        verbose_name_plural = 'Типы проблем'

class HistoryProfileRecords(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    amount = models.IntegerField('Количество изготовленного профиля', default=0)
    profile_sum = models.IntegerField('Всего профиля на данный момент', default=0)
    created_at = models.DateTimeField('Фактическая дата и время списания', default=django.utils.timezone.now)
    
    class Meta:  
        get_latest_by = 'id'
  

class Tasks(models.Model):
    """Модель задач производства"""
    task_name = models.CharField('Наименование', max_length=250)
    task_timedate_start = models.DateTimeField('Дата и время начала', null=True, blank=True)
    task_timedate_end = models.DateTimeField('Дата и время окончания', null=True, blank=True)
    task_profile_type = models.ForeignKey('ProfileType', null=True, on_delete=models.SET_NULL, verbose_name='Тип профиля')
    task_workplace = models.ForeignKey(Workplace, null=True, on_delete=models.SET_NULL, verbose_name='Рабочее место')
    task_profile_amount = models.BigIntegerField('Количество')
    task_comments = models.TextField('Комментарий', blank=True, default='', null=True)
    task_status = models.ForeignKey('TaskStatus', null=True, on_delete=models.SET_NULL, verbose_name='Статус')
    task_user_created = models.CharField('Кто создал задачу', max_length=250, default='Неизвестный пользователь')
    task_timedate_start_fact = models.DateTimeField('Фактическая дата и время начала', null=True, blank=True)
    task_timedate_end_fact = models.DateTimeField('Фактическая дата и время окончания', null=True, blank=True)
    task_is_vision = models.BooleanField('Видимость задачи', default=True)
    task_time_settingUp = models.DateTimeField('Фактическая дата и время начала наладки', null=True, blank=True)
    profile_amount_now = models.BigIntegerField('Количество профиля текущего', default=0)
    task_profile_length = models.FloatField('Длина профиля', default=0)
    worker_accepted_task = models.TextField('ФИО рабочего', blank=True)
    history_offs_shtrips = models.ManyToManyField(OffsShtrips)
    task_profile_material = models.ForeignKey('SteelType', null=True, on_delete=models.SET_NULL, verbose_name='Тип материала')
    history_event_messages = models.ManyToManyField(HistoryEvent)
    history_profile_records = models.ManyToManyField(HistoryProfileRecords)
    sensor_true = models.BooleanField(default=False)
    last_update = models.DateTimeField('Последнее изменение количества профиля в задаче', null=True, blank=True)
    created_at = models.DateTimeField('Дата создания задачи', default=django.utils.timezone.now)
    
    def __str__(self):
        return self.task_name
    
    def is_accepted_video(self):
        """Проверяет, поддерживается ли видеораспознавание для данного типа профиля"""
        return self.task_profile_type.is_accepted_video

    def get_all_history_shtrips(self):
        offs_shtrips = Tasks.objects.get(id=self.id).history_offs_shtrips.all()
        
        return offs_shtrips

    def get_all_history_event_message(self):
        event_messages = Tasks.objects.get(id=self.id).history_event_messages.all()
        return event_messages      
    
    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'


class AcceptedProfile(models.Model):
    """Модель принятых профилей для видеораспознавания"""
    type_profile = models.CharField('Общий тип профиля', max_length=50)
    names_profile = models.TextField('Входящий тип профиля', blank=True, default='', null=True)
    
    def __str__(self):
        return f'{self.type_profile} - {self.names_profile}'
    
    class Meta:
        verbose_name = 'Принятый профиль'
        verbose_name_plural = 'Принятые профили'
