from .models import *
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms.widgets import DateTimeInput, TextInput, Select
from django.db.models import Q
from datetime import datetime


class NewTaskForm(forms.Form):  
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and user.production_area_id:
            self.fields['task_workplace'].queryset = Workplace.objects.filter(
                production_area_id=user.production_area_id
            )
        else:
            self.fields['task_workplace'].queryset = Workplace.objects.none()


    task_name = forms.CharField(max_length=150, widget=TextInput(attrs={"class":"popup-content-block__task-title__input"}), initial='Изготовить профиль')
    task_timedate_start = forms.DateTimeField(label="Время начала", required=True,   widget=DateTimeInput(format="%Y-%m-%d %H:%M", 
                                                                                                          attrs={'type': 'datetime-local',
                                                                                                                 "class":"popup-content-block__time-to-start__input"}),
                                              input_formats=["%Y-%m-%d %H:%m"], initial=datetime.now) 
    task_timedate_end = forms.DateTimeField(label="Время окончания", required=True,   widget=DateTimeInput(format="%Y-%m-%d %H:%M",
                                                                                                           attrs={'type': 'datetime-local',
                                                                                                                  "class":"popup-content-block__time-to-end__input"}),
        input_formats=["%Y-%m-%d %H:%m"])
    task_profile_type = forms.ModelChoiceField(queryset=ProfileType.objects.all())
    task_workplace =  forms.ModelChoiceField(queryset=Workplace.objects.none())
    task_profile_amount = forms.IntegerField()
    task_profile_length = forms.FloatField()
    task_order_number = forms.CharField(max_length=100)
    task_profile_material = forms.FloatField(required=False)
    task_coating_type = forms.ModelChoiceField(queryset=CoatingType.objects.all(), required=False)
    task_coating_area = forms.FloatField(required=False)
    task_coating_thickness = forms.CharField(max_length=100, required=False)
    task_comments = forms.CharField(widget=forms.Textarea(attrs={"class":"new-task-popup-comments__input", 'style':'resize:none;'}), required=False)
    
    class Meta:
        model = Tasks
        
class EditTaskForm(forms.Form):  

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        queryset = Workplace.objects.none()
        if user and user.production_area_id:
            queryset = Workplace.objects.filter(
                production_area_id=user.production_area_id
            )

        selected_workplace_id = None
        if self.is_bound:
            selected_workplace_id = self.data.get('task_workplace')
        else:
            selected_workplace_id = self.initial.get('task_workplace')

        if hasattr(selected_workplace_id, 'id'):
            selected_workplace_id = selected_workplace_id.id

        if selected_workplace_id:
            queryset = Workplace.objects.filter(
                Q(id=selected_workplace_id) | Q(id__in=queryset.values('id'))
            ).distinct()

        self.fields['task_workplace'].queryset = queryset


    task_name = forms.CharField(max_length=150, widget=TextInput(attrs={"class":"popup-content-block__task-title__input"}))
    task_timedate_start = forms.DateTimeField(label="Время начала", required=True,   widget=DateTimeInput(format="%Y-%m-%d %H:%M", 
                                                                                                          attrs={'type': 'datetime-local',
                                                                                                                 "class":"popup-content-block__time-to-start__input"}),
                                              input_formats=["%Y-%m-%d %H:%m"]) 
    task_timedate_end = forms.DateTimeField(label="Время окончания", required=True,   widget=DateTimeInput(format="%Y-%m-%d %H:%M",
                                                                                                           attrs={'type': 'datetime-local',
                                                                                                                  "class":"popup-content-block__time-to-end__input"}),
        input_formats=["%Y-%m-%d %H:%m"])
    task_profile_type = forms.ModelChoiceField(queryset=ProfileType.objects.all())
    task_workplace =  forms.ModelChoiceField(queryset=Workplace.objects.none())
    task_profile_amount = forms.IntegerField()
    task_profile_length = forms.FloatField()
    task_order_number = forms.CharField(max_length=100)
    task_profile_material = forms.FloatField(required=False)
    task_coating_type = forms.ModelChoiceField(queryset=CoatingType.objects.all(), required=False)
    task_coating_area = forms.FloatField(required=False)
    task_coating_thickness = forms.CharField(max_length=100, required=False)
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
