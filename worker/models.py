from django.db import models
from login import models as login_model
from django.contrib.postgres.fields import HStoreField

class WorkerTypeProblem(models.Model):
  name_problem = models.CharField('Наименование типа проблемы', max_length=500)
  
  def __str__(self):
    return str(self.name_problem) 
class Users_analytics(models.Model):
  userId =  models.ForeignKey(login_model.User, null=True, on_delete=models.SET_NULL)
  settingUp = HStoreField('Количество времени на переналадку', null=True)
  profile_amount = HStoreField('Количество изготовленного профиля по датам', null=True)
  work_time = HStoreField('Время полезной работы', null=True)
  
  def __str__(self):
    return self.userId
