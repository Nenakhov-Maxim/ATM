from django import template
import math
from datetime import datetime, timedelta

register = template.Library()

@register.filter(name='date_to_chel')
def split(date):
  """
    Возвращает значение +5 часов от UTC
  """
  new_date = date + timedelta(hours=5)
  return new_date