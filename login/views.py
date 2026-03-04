from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse
from .forms import LoginForm
from .utils import DataMixin
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import User


def get_redirect_url_for_user(user):
  """Return start page by role: worker-only -> worker app, others -> services panel."""
  if is_worker_only(user):
    return reverse('worker')
  return reverse('services_panel')


def is_worker_only(user):
  perms = user.get_group_permissions()
  has_worker_perm = 'worker.change_workertypeproblem' in perms
  has_master_perms = any(perm.startswith('master.') for perm in perms)
  return has_worker_perm and not has_master_perms and not user.is_superuser and not user.is_staff


class LoginUser(LoginView):
  form_class = LoginForm
  template_name = 'login.html'
  extra_context = {'title': 'Авторизация'}
    
  
  def get_success_url(self):    
    return get_redirect_url_for_user(self.request.user)


def root_redirect(request):
  if not request.user.is_authenticated:
    return redirect('users:login')
  return redirect(get_redirect_url_for_user(request.user))
 

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
        redirect_url = get_redirect_url_for_user(user)
        
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
