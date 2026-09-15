from django.db.models import Prefetch, Q
from django.utils import timezone

from .history_utils import profile_record_user_display_name
from .models import HistoryProfileRecords, OffsShtrips, Tasks
from .report import create_excel_from_dict_list, profile_name_with_length_group
from .report_periods import REPORT_TIME_ZONE, period_query


def completed_work_rows(periods, user):
    records = HistoryProfileRecords.objects.filter(period_query(periods)).select_related('user').order_by('created_at', 'id')
    strips = OffsShtrips.objects.filter(period_query(periods)).select_related('type_value_id').order_by('created_at', 'id')
    tasks = Tasks.objects.filter(
        Q(production_area=user.production_area_id) | Q(task_workplace__production_area_id=user.production_area_id),
        history_profile_records__in=records,
    ).distinct().select_related('task_profile_type').prefetch_related(
        Prefetch('history_profile_records', queryset=records, to_attr='report_records'),
        Prefetch('history_offs_shtrips', queryset=strips, to_attr='report_strips'),
    ).order_by('id')
    result = {}
    for task in tasks:
        totals = {}
        for record in task.report_records:
            name = profile_record_user_display_name(record, task)
            key = record.user_id, name
            totals[key] = totals.get(key, 0) + record.amount
        strip_values = '; '.join(f'{record.value}' + ('' if record.type_value_id_id == 1 else '(п.м.)') for record in task.report_strips)
        created = timezone.localtime(task.created_at, REPORT_TIME_ZONE)
        result[task.pk] = {
            'label': f'Задача ID № {task.pk} от {created}. Списаны штрипсы: {strip_values}',
            'data': [[name, task.task_workplace_id, profile_name_with_length_group(task.task_profile_type.profile_name, task.task_profile_length),
                      amount * task.task_profile_length, '8', '0', 'Да', ''] for (_, name), amount in totals.items()],
        }
    return result


def create_completed_work_report(periods, user, output_filename, period_label=None):
    headers = ['Ф.И.О', 'Номер линии', 'Марка изделия', 'Общее кол-во п/м', 'Отработанные часы', 'Ср. зд.', 'Хоз. работы', 'Подпись работника']
    return create_excel_from_dict_list(headers, completed_work_rows(periods, user), output_filename, period_label=period_label)
