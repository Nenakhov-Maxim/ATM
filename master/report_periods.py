from functools import reduce
from operator import or_
from uuid import uuid4

from django import forms
from django.db.models import Q
from django.utils import timezone

from .shifts import PRODUCTION_TIME_ZONE, SHIFT_CHOICES, current_production_date, shift_bounds


REPORT_TIME_ZONE = PRODUCTION_TIME_ZONE


def period_query(periods, field='created_at'):
    return reduce(or_, (Q(**{f'{field}__gte': start, f'{field}__lt': end}) for start, end in periods), Q(pk__in=[]))


def report_filename(document, selection):
    return f"{document} {selection['period_label'].replace(':', '-')}_{uuid4().hex[:8]}.xlsx"


class ReportForm(forms.Form):
    report_mode = forms.ChoiceField(
        choices=(('period', 'Дата и время'), ('shifts', 'Смены за день')),
        initial='period', widget=forms.RadioSelect,
    )
    date_start = forms.DateTimeField(required=False, widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}))
    date_end = forms.DateTimeField(required=False, widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}))
    production_date = forms.DateField(required=False, initial=current_production_date, widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    report_shifts = forms.TypedMultipleChoiceField(required=False, choices=SHIFT_CHOICES, coerce=int, widget=forms.CheckboxSelectMultiple)

    def __init__(self, data=None, *args, **kwargs):
        if data is not None:
            data = data.copy()
            if not data.get('report_mode'):
                data['report_mode'] = 'period'
        super().__init__(data, *args, **kwargs)
        mode = self.data.get('report_mode', 'period') if self.is_bound else 'period'
        for name in ('date_start', 'date_end'):
            self.fields[name].required = mode == 'period'
            self.fields[name].disabled = mode == 'shifts'
        for name in ('production_date', 'report_shifts'):
            self.fields[name].required = mode == 'shifts'
            # Bound inactive fields must not invalidate the selected report mode.
            self.fields[name].disabled = self.is_bound and mode == 'period'

    def clean(self):
        data = super().clean()
        if data.get('report_mode') == 'shifts':
            day, shifts = data.get('production_date'), data.get('report_shifts')
            if day and shifts:
                shifts = sorted(set(shifts))
                data['report_shifts'] = shifts
                data['periods'] = [shift_bounds(day, shift) for shift in shifts]
                data['date_start'], data['date_end'] = data['periods'][0][0], data['periods'][-1][1]
                data['period_label'] = f"{day:%d.%m.%Y}, смены {', '.join(map(str, shifts))}"
        elif data.get('report_mode') == 'period':
            # datetime-local carries plant wall time, independent of the active Django timezone.
            for field in ('date_start', 'date_end'):
                value = data.get(field)
                if value is not None:
                    data[field] = timezone.make_aware(value.replace(tzinfo=None), REPORT_TIME_ZONE)
            start, end = data.get('date_start'), data.get('date_end')
            if start and end:
                if end <= start:
                    self.add_error('date_end', 'Окончание периода должно быть позже начала.')
                else:
                    data['periods'] = [(start, end)]
                    data['period_label'] = f'{start:%d.%m.%Y %H:%M} - {end:%d.%m.%Y %H:%M}'
        return data
