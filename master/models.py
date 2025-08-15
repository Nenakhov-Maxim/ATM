from django.db import models
from django.contrib.postgres.fields import HStoreField


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


class ProfileType(models.Model):
    """Модель типов профилей"""
    profile_name = models.CharField('Наименование', max_length=100)
    association_name = models.CharField('Общее название', blank=True, default='', null=True, max_length=100)
    is_accepted_video = models.BooleanField('Доступно для видео?', default=False, null=True)
    
    def __str__(self):
        return self.profile_name
    
    class Meta:
        verbose_name = 'Тип профиля'
        verbose_name_plural = 'Типы профилей'


class Workplace(models.Model):
    """Модель рабочих мест"""
    workplace_name = models.CharField('Наименование рабочего места', max_length=250)
    type_of_equipment = models.CharField('Наименование оборудования', max_length=250)
    inv_number = models.IntegerField('Инвентарный номер оборудования')
    
    def __str__(self):
        return self.workplace_name
    
    class Meta:
        verbose_name = 'Рабочее место'
        verbose_name_plural = 'Рабочие места'


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
  
  

class Tasks(models.Model):
    """Модель задач производства"""
    task_name = models.CharField('Наименование', max_length=250)
    task_timedate_start = models.DateTimeField('Дата и время начала', null=True, blank=True)
    task_timedate_end = models.DateTimeField('Дата и время окончания', null=True, blank=True)
    task_profile_type = models.ForeignKey('ProfileType', null=True, on_delete=models.SET_NULL, verbose_name='Тип профиля')
    task_workplace = models.ForeignKey('Workplace', null=True, on_delete=models.SET_NULL, verbose_name='Рабочее место')
    task_profile_amount = models.BigIntegerField('Количество')
    task_comments = models.TextField('Комментарий', blank=True, default='', null=True)
    task_status = models.ForeignKey('TaskStatus', null=True, on_delete=models.SET_NULL, verbose_name='Статус')
    task_user_created = models.CharField('Кто создал задачу', max_length=250, default='Неизвестный пользователь')
    task_history = models.ForeignKey('TaskHistory', on_delete=models.CASCADE, verbose_name='История')
    task_timedate_start_fact = models.DateTimeField('Фактическая дата и время начала', null=True, blank=True)
    task_timedate_end_fact = models.DateTimeField('Фактическая дата и время окончания', null=True, blank=True)
    task_is_vision = models.BooleanField('Видимость задачи', default=True)
    task_time_settingUp = models.DateTimeField('Фактическая дата и время начала наладки', null=True, blank=True)
    profile_amount_now = models.BigIntegerField('Количество профиля текущего', default=0)
    task_profile_length = models.FloatField('Длина профиля', default=0)
    worker_accepted_task = models.TextField('ФИО рабочего', blank=True)
    
    def __str__(self):
        return self.task_name
    
    def is_accepted_video(self):
        """Проверяет, поддерживается ли видеораспознавание для данного типа профиля"""
        if not self.task_profile_type or not self.task_profile_type.association_name:
            return False
            
        accepted_profiles = AcceptedProfile.objects.filter(
            type_profile=self.task_profile_type.association_name
        )
        
        if not accepted_profiles.exists():
            return False
            
        for profile in accepted_profiles:
            if self.task_profile_type.profile_name in profile.names_profile.split(','):
                return True
        return False
    
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
