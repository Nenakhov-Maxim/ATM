from .models import *
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms.widgets import TextInput, Select
from .access import available_workplaces, available_areas

from .shifts import SHIFT_CHOICES, current_production_date, shift_bounds
from .report_periods import ReportForm, REPORT_TIME_ZONE


class TaskScheduleForm(forms.Form):
    task_area = forms.ModelChoiceField(queryset=ProductionArea.objects.none(), required=False, label="Участок", empty_label="Все доступные участки")
    allow_stock = forms.BooleanField(label='Разрешить изготовление на склад', required=False)
    task_shift_date = forms.DateField(
        label='Дата производственных суток',
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        initial=current_production_date,
    )
    task_shift = forms.TypedChoiceField(
        label='Плановая смена', choices=(('', 'Выберите смену'),) + SHIFT_CHOICES, coerce=int,
    )

    def clean(self):
        data = super().clean()
        if data.get('task_shift_date') and data.get('task_shift'):
            data['task_timedate_start'], data['task_timedate_end'] = shift_bounds(
                data['task_shift_date'], data['task_shift'],
            )
        if data.get("task_area") and data.get("task_workplace"):
            if data["task_workplace"].production_area_id_id != data["task_area"].pk:
                self.add_error("task_workplace", "Рабочее место не относится к выбранному участку.")
        return data


class WorkplaceChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.production_area_id} — {obj.workplace_name}'


class NewTaskForm(TaskScheduleForm):
    allow_stock = forms.BooleanField(label='Разрешить изготовление на склад', required=False, initial=True)
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['task_workplace'].queryset = available_workplaces(user)
        self.fields['task_area'].queryset = available_areas(user)


    task_name = forms.CharField(max_length=150, widget=TextInput(attrs={"class":"popup-content-block__task-title__input"}), initial='Изготовить профиль')
    task_profile_type = forms.ModelChoiceField(queryset=ProfileType.objects.order_by('profile_name', 'pk'))
    task_workplace = WorkplaceChoiceField(queryset=Workplace.objects.none())
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
        
class EditTaskForm(TaskScheduleForm):
    id_task = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        for name in ('task_shift_date', 'task_shift', 'allow_stock', 'task_area'):
            self.fields[name].widget.attrs['id'] = f'id_edit_{name}'

        self.fields['task_workplace'].queryset = available_workplaces(user)
        self.fields['task_area'].queryset = available_areas(user)


    task_name = forms.CharField(max_length=150, widget=TextInput(attrs={"class":"popup-content-block__task-title__input"}))
    task_profile_type = forms.ModelChoiceField(queryset=ProfileType.objects.order_by('profile_name', 'pk'))
    task_workplace = WorkplaceChoiceField(queryset=Workplace.objects.none())
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
