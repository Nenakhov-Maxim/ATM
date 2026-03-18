from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import HStoreField
from django.db import models
# from master.models import Workplace

class Workplace(models.Model):
    """Модель рабочих мест"""
    workplace_name = models.CharField('Наименование рабочего места', max_length=250)
    type_of_equipment = models.CharField('Наименование оборудования', max_length=250)
    inv_number = models.IntegerField('Инвентарный номер оборудования')
    production_area_id = models.ForeignKey('ProductionArea',  null=True, on_delete=models.SET_NULL, blank=True)
    
    def __str__(self):
        return self.workplace_name
class ProductionArea(models.Model):
  """Модель производственных участков"""
  production_area_name = models.CharField(max_length=150, verbose_name='Наименование производственного участка')
  
  def __str__(self):
    return self.production_area_name
  

class User(AbstractUser):
  position_id = models.ForeignKey('UserDepPosition', on_delete=models.SET_NULL, null=True,)
  production_area_id = models.ForeignKey('ProductionArea',  null=True, on_delete=models.SET_NULL, blank=True)
  production_area = models.CharField(max_length=100, verbose_name='Производственный участок')
  access_page = models.CharField(max_length=100, verbose_name='Перечень страниц для доступа')
  qr_code = models.CharField(max_length=255, unique=True, null=True, blank=True, verbose_name='QR-код для входа')
  

class UserDepPosition(models.Model):
  position = models.CharField(max_length=100, verbose_name='Должность')
  
  def __str__(self):
    return self.position


