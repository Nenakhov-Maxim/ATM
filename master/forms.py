from .models import *
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms.widgets import TextInput, Select
from django.db.models import Q

from .shifts import SHIFT_CHOICES, current_production_date, shift_bounds
from .report_periods import ReportForm, REPORT_TIME_ZONE


class TaskScheduleForm(forms.Form):
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
        return data


class NewTaskForm(TaskScheduleForm):
    allow_stock = forms.BooleanField(label='Разрешить изготовление на склад', required=False, initial=True)
    
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
        
class EditTaskForm(TaskScheduleForm):
    id_task = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        for name in ('task_shift_date', 'task_shift', 'allow_stock'):
            self.fields[name].widget.attrs['id'] = f'id_edit_{name}'

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
