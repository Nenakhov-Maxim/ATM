from .models import *
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms.widgets import DateTimeInput, TextInput, Select
from datetime import datetime


class NewTaskForm(forms.Form):  
   
    task_name = forms.CharField(max_length=150, widget=TextInput(attrs={"class":"popup-content-block__task-title__input"}), initial='Изготовить профиль')
    task_timedate_start = forms.DateTimeField(label="Время начала", required=True,   widget=DateTimeInput(format="%Y-%m-%d %H:%M", 
                                                                                                          attrs={'type': 'datetime-local',
                                                                                                                 "class":"popup-content-block__time-to-start__input"}),
                                              input_formats=["%Y-%m-%d %H:%m"], initial=datetime.now) 
    task_timedate_end = forms.DateTimeField(label="Время окончания", required=True,   widget=DateTimeInput(format="%Y-%m-%d %H:%M",
                                                                                                           attrs={'type': 'datetime-local',
                                                                                                                  "class":"popup-content-block__time-to-end__input"}),
        input_formats=["%Y-%m-%d %H:%m"])
    task_profile_type = forms.ModelChoiceField(queryset=Profile_type.objects.all())
    task_workplace =  forms.ModelChoiceField(queryset=Workplace.objects.all())
    task_profile_amount = forms.IntegerField()
    task_profile_length = forms.FloatField()
    task_comments = forms.CharField(widget=forms.Textarea(attrs={"class":"new-task-popup-comments__input", 'style':'resize:none;'}), required=False)
    
    class Meta:
        model = Tasks
        
class EditTaskForm(forms.Form):  
   
    task_name = forms.CharField(max_length=150, widget=TextInput(attrs={"class":"popup-content-block__task-title__input"}))
    task_timedate_start = forms.DateTimeField(label="Время начала", required=True,   widget=DateTimeInput(format="%Y-%m-%d %H:%M", 
                                                                                                          attrs={'type': 'datetime-local',
                                                                                                                 "class":"popup-content-block__time-to-start__input"}),
                                              input_formats=["%Y-%m-%d %H:%m"]) 
    task_timedate_end = forms.DateTimeField(label="Время окончания", required=True,   widget=DateTimeInput(format="%Y-%m-%d %H:%M",
                                                                                                           attrs={'type': 'datetime-local',
                                                                                                                  "class":"popup-content-block__time-to-end__input"}),
        input_formats=["%Y-%m-%d %H:%m"])
    task_profile_type = forms.ModelChoiceField(queryset=Profile_type.objects.all())
    task_workplace =  forms.ModelChoiceField(queryset=Workplace.objects.all())
    task_profile_amount = forms.IntegerField()
    task_profile_length = forms.FloatField()
    task_comments = forms.CharField(widget=forms.Textarea(attrs={"class":"new-task-popup-comments__input", 'style':'resize:none;'}))
    
    class Meta:
        model = Tasks
        
class PauseTaskForm(forms.Form):
    problem_type = forms.ModelChoiceField(queryset=MasterTypeProblem.objects.all(), widget=Select(attrs={"class":"pause_task_popup__cat-problem"}))
    problem_comments = forms.CharField(widget=forms.Textarea(attrs={"class":"pause_task_popup__comment", 'style':'resize:none;'}))
    
class LoginForm(AuthenticationForm):
    pass

class ReportForm(forms.Form):
    date_start = forms.DateTimeField(widget=DateTimeInput(format="%Y-%m-%d %H:%M",
                                                      attrs={'type': 'datetime-local',
                                                            "class":"popup-content-block__time-to-end__input"}))
    date_end = forms.DateTimeField(widget=DateTimeInput(format="%Y-%m-%d %H:%M",
                                                      attrs={'type': 'datetime-local',
                                                            "class":"popup-content-block__time-to-end__input"}))
   