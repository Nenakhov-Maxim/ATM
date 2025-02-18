from django.contrib import admin
import django.contrib
import django.contrib.auth
import django.contrib.auth.urls
from django.urls import path, include
import django
from django.conf.urls import include
from django.contrib import admin
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'analytics'

urlpatterns = [       
    path('', views.get_home_page, name='analitytics-home'),
    path('update-chart/<str:type_chart>/<int:filter>/', views.update_chart, name='update-chart'),       
]
 