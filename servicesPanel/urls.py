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
    path('', views.services_panel_home, name='services_panel'),
]
