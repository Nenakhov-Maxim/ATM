from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import HStoreField
from django.db import models
from master import models as master_models

class User(AbstractUser):
  position_id = models.ForeignKey('UserDepPosition', on_delete=models.SET_NULL, null=True,)
  production_area_id = models.ForeignKey(master_models.Workplace,  null=True, on_delete=models.SET_NULL)
  production_area = models.CharField(max_length=100, verbose_name='Производственный участок')
  access_page = models.CharField(max_length=100, verbose_name='Перечень страниц для доступа')
  

class UserDepPosition(models.Model):
  position = models.CharField(max_length=100, verbose_name='Должность')
  
  def __str__(self):
    return self.position
  
