from django.contrib import admin
import django.contrib
import django.contrib.auth
import django.contrib.auth.urls
from django.urls import path, include
import django
from django.conf.urls import include
from django.contrib import admin
from . import views


urlpatterns = [    
    path('', views.master_home, name='master'),
    path('start_task/', views.start_task, name='start_task'),
    path('pause_task/<int:id_task>', views.pause_task, name='pause_task'),
    path('new_task/', views.new_task, name='new_task'),
    path('delete_task/', views.delete_task, name='new_task'),
    path('edit_task/', views.edit_task, name='edit_task'),
    path('hide_task/', views.hide_task, name='edit_task'),
    path('new_report/', views.new_report, name='new_report'),
    path('get-material/', views.get_material, name='get_material'),  
]
