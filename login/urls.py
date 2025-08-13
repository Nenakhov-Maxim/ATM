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

app_name = 'users'

urlpatterns = [    
    path('login/', views.LoginUser.as_view(redirect_authenticated_user=True), name='login'),
    path('', views.LoginUser.as_view(redirect_authenticated_user=True), name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('qr-login/', views.qr_login, name='qr_login'),
]
