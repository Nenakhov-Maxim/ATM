from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse_lazy, reverse
from .forms import LoginForm
from .utils import DataMixin
from django.contrib.auth import authenticate, login, logout


class LoginUser(LoginView):
  form_class = LoginForm
  template_name = 'login.html'
  extra_context = {'title': 'Авторизация'}
    
  
  def get_success_url(self):    
    if self.request.user.is_superuser:
      # print('Перенаправляем на admin-панель')
      return reverse_lazy('admin:index')
    elif 'master.view_tasks' in self.request.user.get_group_permissions():      
      # print('Перенаправляем на master')
      return reverse_lazy('master')
    elif 'worker.change_workertypeproblem' in self.request.user.get_group_permissions():      
      # print('Перенаправляем на worker')
      return reverse_lazy('worker')    
 

def logout_user(request):
  logout(request)
  return HttpResponseRedirect(reverse('users:login'))

  
  

        