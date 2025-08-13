from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse_lazy, reverse
from .forms import LoginForm
from .utils import DataMixin
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import User


class LoginUser(LoginView):
  form_class = LoginForm
  template_name = 'login.html'
  extra_context = {'title': 'Авторизация'}
    
  
  def get_success_url(self):    
    if self.request.user.is_superuser:
      # 'Перенаправляем на admin-панель'
      return reverse_lazy('admin:index')
    elif 'master.view_tasks' in self.request.user.get_group_permissions():      
      # 'Перенаправляем на master'
      return reverse_lazy('master')
    elif 'worker.change_workertypeproblem' in self.request.user.get_group_permissions():      
      # 'Перенаправляем на worker'
      return reverse_lazy('worker')    
 

@csrf_exempt
@require_http_methods(["POST"])
def qr_login(request):
    """
    Обработка входа по QR-коду
    """
    try:
        data = json.loads(request.body)
        qr_code = data.get('qr_code', '').strip()
        
        if not qr_code:
            return JsonResponse({
                'success': False, 
                'error': 'QR-код не может быть пустым'
            })
        
        # Поиск пользователя по QR-коду
        try:
            user = User.objects.get(qr_code=qr_code, is_active=True)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': 'Пользователь с таким QR-кодом не найден'
            })
        
        # Аутентификация пользователя
        login(request, user)
        
        # Определение URL для перенаправления
        if user.is_superuser:
            redirect_url = reverse('admin:index')
        elif 'master.view_tasks' in user.get_group_permissions():
            redirect_url = reverse('master')
        elif 'worker.change_workertypeproblem' in user.get_group_permissions():
            redirect_url = reverse('worker')
        else:
            redirect_url = reverse('users:login')
        
        return JsonResponse({
            'success': True,
            'redirect_url': redirect_url,
            'message': f'Добро пожаловать, {user.get_full_name() or user.username}!'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'error': 'Неверный формат данных'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Произошла ошибка: {str(e)}'
        })


def logout_user(request):
  logout(request)
  return HttpResponseRedirect(reverse('users:login'))
