from master.models import *
from .models import WorkerTypeProblem
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms.widgets import DateTimeInput, TextInput, Select

class PauseTaskForm(forms.Form):
    problem_type = forms.ModelChoiceField(queryset=WorkerTypeProblem.objects.all(), widget=Select(attrs={"class":"pause_task_popup__cat-problem"}))
    problem_comments = forms.CharField(widget=forms.Textarea(attrs={"class":"pause_task_popup__comment", 'style':'resize:none;'}))
    task_id = forms.IntegerField()
    
class DenyTaskForm(forms.Form):
    problem_type = forms.ModelChoiceField(queryset=WorkerTypeProblem.objects.all(), widget=Select(attrs={"class":"pause_task_popup__cat-problem"}))
    problem_comments = forms.CharField(widget=forms.Textarea(attrs={"class":"pause_task_popup__comment", 'style':'resize:none;'}))
    task_id = forms.IntegerField()