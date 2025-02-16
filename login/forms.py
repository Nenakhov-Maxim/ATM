from .models import *
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms.widgets import DateTimeInput, TextInput, Select
from django.contrib.auth import get_user_model

  
class LoginForm(AuthenticationForm):
    username = forms.CharField(label='ID пользователя', max_length=150, widget=forms.TextInput(attrs={'class': 'textbox__item textbox-id', 'placeholder': 'Введите ID пользователя'}))
    password = forms.CharField(label='Пароль', max_length=150, widget=forms.PasswordInput(attrs={'class': 'textbox__item', 'placeholder': 'Введите пароль'}))
    
    class Meta:
        model = get_user_model()
        fields = ['username', 'password']