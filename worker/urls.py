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
    
    path('', views.worker_home, name='worker'),
    path('start_working/', views.start_working, name='start_working'),
    path('month/start_working/', views.start_working, name='month_start_working'),
    path('week/start_working/', views.start_working, name='week_start_working'),
    path('now/start_working/', views.start_working, name='now_start_working'),
    path('now/', views.task_now, name='now_filter'),
    path('week/', views.task_week, name='week_filter'),
    path('month/', views.task_month, name='month_filter'),
    path('pause_task/', views.pause_task, name='pause_working'),
    path('deny_task/', views.deny_task, name='deny_working'),
    path('complete_task/', views.complete_task, name='complete_working'),
    path('setting-up/', views.start_settingUp, name='settingUp'),
    path('edit-profile-amount-value/', views.edit_profile_amount, name='change_profile_amount'),
    path('shiftChange/', views.shiftChange, name='change_worker'),
        
]
