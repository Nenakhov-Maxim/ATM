import os
from collections import OrderedDict, defaultdict
from datetime import datetime, time, timedelta

from django.db.models import Prefetch, Q
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from .models import HistoryProfileRecords, OffsShtrips, SteelTypeProfile, Tasks


SHIFT_1 = 'shift_1'
SHIFT_2 = 'shift_2'
SHIFT_3 = 'shift_3'
SHIFT_KEYS = (SHIFT_1, SHIFT_2, SHIFT_3)


def create_profiling_invoice_report(start_date, end_date, user, output_filename=None):
    if not os.path.exists('excel_files'):
        os.makedirs('excel_files')

    if output_filename is None:
        output_filename = f'Накладная на линию профилирования от {datetime.now().date()}.xlsx'

    filepath = os.path.join('excel_files', output_filename)
    tasks = _get_completed_tasks(start_date, end_date, user)
    rows = _build_report_rows(tasks, start_date, end_date)
    _write_workbook(filepath, rows, start_date, end_date)
    return filepath


def _get_completed_tasks(start_date, end_date, user):
    return Tasks.objects.filter(
        Q(task_status_id=2) &
        Q(task_timedate_end_fact__range=(start_date, end_date)) &
        Q(
            Q(production_area=user.production_area_id) |
            Q(task_workplace__production_area_id=user.production_area_id)
        )
    ).select_related(
        'task_profile_type',
        'task_profile_material',
        'task_coating_type',
        'task_coating_thickness',
    ).prefetch_related(
        Prefetch(
            'history_profile_records',
            queryset=HistoryProfileRecords.objects.select_related('user').order_by('created_at', 'id'),
        ),
        Prefetch(
            'history_offs_shtrips',
            queryset=OffsShtrips.objects.select_related('type_value_id').order_by('created_at', 'id'),
        ),
    ).order_by('task_profile_type__profile_name', 'task_profile_length', 'id')


def _build_report_rows(tasks, start_date, end_date):
    profile_groups = OrderedDict()
    material_weight_cache = {}

    for task in tasks:
        profile_key = task.task_profile_type_id
        profile_group = profile_groups.setdefault(profile_key, _empty_profile_group(task))
        detail_key = _task_group_key(task)
        detail_row = profile_group['details'].setdefault(detail_key, _empty_detail_row(task))

        profile_amounts = _profile_amounts_by_shift(task, start_date, end_date)
        if not any(profile_amounts.values()):
            profile_amounts[_shift_key(task.task_timedate_end_fact)] += task.profile_amount_now or task.task_profile_amount

        for shift_key, amount in profile_amounts.items():
            detail_row['profile_by_shift'][shift_key] += amount
            profile_group['profile_by_shift'][shift_key] += amount

        shtrips_by_shift = _shtrips_by_shift(task, start_date, end_date, material_weight_cache)
        for shift_key, weight in shtrips_by_shift.items():
            detail_row['shtrips_by_shift'][shift_key] += weight
            profile_group['shtrips_by_shift'][shift_key] += weight

    return list(profile_groups.values())


def _empty_profile_group(task):
    return {
        'profile_name': task.task_profile_type.profile_name,
        'shtrips_name': task.task_profile_type.association_name_shtrips,
        'profile_by_shift': defaultdict(float),
        'shtrips_by_shift': defaultdict(float),
        'details': OrderedDict(),
    }


def _empty_detail_row(task):
    return {
        'coating': _coating_label(task),
        'profile_length': task.task_profile_length or 0,
        'profile_by_shift': defaultdict(float),
        'shtrips_by_shift': defaultdict(float),
    }


def _task_group_key(task):
    return (
        task.task_profile_type_id,
        round(float(task.task_profile_length or 0), 3),
        task.task_coating_type_id,
        task.task_coating_thickness_id,
        task.task_coating_area,
    )


def _coating_label(task):
    if not task.task_coating_type:
        return ''

    return str(task.task_coating_type)


def _profile_amounts_by_shift(task, start_date, end_date):
    amounts = defaultdict(float)
    for record in task.history_profile_records.all():
        if start_date <= record.created_at <= end_date:
            amounts[_shift_key(record.created_at)] += record.amount
    return amounts


def _shtrips_by_shift(task, start_date, end_date, material_weight_cache):
    amounts = defaultdict(float)
    shtrips_items = list(task.history_offs_shtrips.all())
    in_period_items = [
        shtrips for shtrips in shtrips_items
        if start_date <= shtrips.created_at <= end_date
    ]

    for shtrips in in_period_items or shtrips_items:
        amounts[_shift_key(shtrips.created_at)] += _shtrips_weight_kg(task, shtrips, material_weight_cache)
    return amounts


def _shtrips_weight_kg(task, shtrips, material_weight_cache):
    if shtrips.type_value_id_id == 1:
        return shtrips.value

    cache_key = (task.task_profile_type_id, task.task_profile_material_id)
    if cache_key in material_weight_cache:
        return shtrips.value * material_weight_cache[cache_key]

    try:
        material_weight_cache[cache_key] = SteelTypeProfile.objects.get(
            type_profile=task.task_profile_type,
            type_steel=task.task_profile_material,
        ).weight
    except SteelTypeProfile.DoesNotExist:
        material_weight_cache[cache_key] = None
        return shtrips.value

    material_weight = material_weight_cache[cache_key]
    if material_weight is None:
        return shtrips.value
    return shtrips.value * material_weight


def _shift_key(value):
    local_value = timezone.localtime(value) if timezone.is_aware(value) else value
    current_time = local_value.time()

    if time(8, 0) <= current_time < time(17, 0):
        return SHIFT_1
    if current_time >= time(17, 0):
        return SHIFT_2
    if current_time < time(1, 0):
        return SHIFT_2
    return SHIFT_3


def _write_workbook(filepath, rows, start_date, end_date):
    wb = Workbook()
    ws = wb.active
    ws.title = 'Накладная'

    header_font = Font(bold=True, size=10)
    profile_font = Font(bold=True, size=10)
    detail_font = Font(size=10)
    thin = Side(border_style='thin', color='000000')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left = Alignment(horizontal='left', vertical='center', wrap_text=True)
    detail_left = Alignment(horizontal='left', vertical='center')

    _setup_example_columns(ws)
    _write_example_header(ws, header_font, border, center)

    current_row = 4
    for profile_group in rows:
        _write_profile_group_row(ws, current_row, profile_group, profile_font, border, center, left)
        current_row += 1

        for detail_row in profile_group['details'].values():
            _write_detail_row(ws, current_row, detail_row, detail_font, border, center, detail_left)
            current_row += 1

    _write_total_row(ws, current_row, rows, border, center)
    wb.save(filepath)


def _setup_example_columns(ws):
    for column in range(1, 25):
        ws.column_dimensions[ws.cell(1, column).column_letter].width = 6

    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 5
    ws.column_dimensions['C'].width = 4
    ws.column_dimensions['D'].width = 8


def _write_example_header(ws, header_font, border, center):
    merges = [
        'A1:D3', 'E1:F1', 'G1:H1', 'I1:J1', 'K1:L2', 'M1:N2',
        'O1:P3', 'Q1:R1', 'S1:T1', 'U1:V1', 'W1:X2',
        'E2:F2', 'G2:H2', 'I2:J2', 'Q2:R2', 'S2:T2', 'U2:V2',
        'E3:F3', 'G3:H3', 'I3:J3', 'K3:L3', 'M3:N3',
        'Q3:R3', 'S3:T3', 'U3:V3', 'W3:X3',
    ]
    for cells in merges:
        ws.merge_cells(cells)

    values = {
        'A1': 'Профиль',
        'E1': '1 см.',
        'G1': '2см.',
        'I1': '3см.',
        'K1': 'Всего',
        'M1': 'Всего',
        'O1': 'Штрипс',
        'Q1': '1см.',
        'S1': '2см.',
        'U1': '3см.',
        'W1': 'Всего',
        'E2': 'Кол-во',
        'G2': 'Кол-во ',
        'I2': 'Кол-во',
        'Q2': 'К-во штр.',
        'S2': 'К-во штр.',
        'U2': 'К-во штр.',
        'E3': '(штук)',
        'G3': '(штук)',
        'I3': '(штук)',
        'K3': '(штук)',
        'M3': '(п/м)',
        'Q3': '(кг)',
        'S3': '(кг)',
        'U3': '(кг)',
        'W3': 'м/п',
    }
    for cell, value in values.items():
        ws[cell] = value

    for row in ws.iter_rows(min_row=1, max_row=3, min_col=1, max_col=24):
        for cell in row:
            cell.font = header_font
            cell.border = border
            cell.alignment = center


def _write_profile_group_row(ws, row_number, profile_group, font, border, center, left):
    _merge_data_row(ws, row_number)
    profile_by_shift = profile_group['profile_by_shift']
    shtrips_by_shift = profile_group['shtrips_by_shift']

    ws.cell(row_number, 1).value = profile_group['profile_name']
    ws.cell(row_number, 5).value = _number_or_empty(profile_by_shift[SHIFT_1])
    ws.cell(row_number, 7).value = _number_or_empty(profile_by_shift[SHIFT_2])
    ws.cell(row_number, 9).value = _number_or_empty(profile_by_shift[SHIFT_3])
    ws.cell(row_number, 11).value = _number_or_empty(sum(profile_by_shift.values()))
    ws.cell(row_number, 15).value = profile_group['shtrips_name']
    ws.cell(row_number, 17).value = _number_or_empty(round(shtrips_by_shift[SHIFT_1], 2))
    ws.cell(row_number, 19).value = _number_or_empty(round(shtrips_by_shift[SHIFT_2], 2))
    ws.cell(row_number, 21).value = _number_or_empty(round(shtrips_by_shift[SHIFT_3], 2))
    ws.cell(row_number, 23).value = _number_or_empty(round(sum(shtrips_by_shift.values()), 2))

    _style_data_row(ws, row_number, font, border, center, left)


def _write_detail_row(ws, row_number, detail_row, font, border, center, left):
    _merge_data_row(ws, row_number)
    profile_by_shift = detail_row['profile_by_shift']
    total_amount = sum(profile_by_shift.values())
    total_length = round(total_amount * float(detail_row['profile_length'] or 0), 2)
    shtrips_by_shift = detail_row['shtrips_by_shift']

    ws.cell(row_number, 1).value = detail_row['coating']
    ws.cell(row_number, 3).value = 'L='
    ws.cell(row_number, 4).value = detail_row['profile_length']
    ws.cell(row_number, 5).value = _number_or_empty(profile_by_shift[SHIFT_1])
    ws.cell(row_number, 7).value = _number_or_empty(profile_by_shift[SHIFT_2])
    ws.cell(row_number, 9).value = _number_or_empty(profile_by_shift[SHIFT_3])
    ws.cell(row_number, 11).value = _number_or_empty(total_amount)
    ws.cell(row_number, 13).value = _number_or_empty(total_length)
    ws.cell(row_number, 17).value = _number_or_empty(round(shtrips_by_shift[SHIFT_1], 2))
    ws.cell(row_number, 19).value = _number_or_empty(round(shtrips_by_shift[SHIFT_2], 2))
    ws.cell(row_number, 21).value = _number_or_empty(round(shtrips_by_shift[SHIFT_3], 2))
    ws.cell(row_number, 23).value = _number_or_empty(round(sum(shtrips_by_shift.values()), 2))

    _style_data_row(ws, row_number, font, border, center, left)


def _write_total_row(ws, row_number, rows, border, center):
    _merge_data_row(ws, row_number)
    total_length = 0
    total_shtrips = 0
    for profile_group in rows:
        total_shtrips += sum(profile_group['shtrips_by_shift'].values())
        for detail_row in profile_group['details'].values():
            total_amount = sum(detail_row['profile_by_shift'].values())
            total_length += total_amount * float(detail_row['profile_length'] or 0)

    ws.cell(row_number, 13).value = _number_or_empty(round(total_length, 2))
    ws.cell(row_number, 23).value = _number_or_empty(round(total_shtrips, 2))
    _style_data_row(ws, row_number, Font(bold=True, size=10), border, center, center)


def _merge_data_row(ws, row_number):
    for start_column in range(5, 25, 2):
        ws.merge_cells(
            start_row=row_number,
            start_column=start_column,
            end_row=row_number,
            end_column=start_column + 1,
        )


def _style_data_row(ws, row_number, font, border, center, left):
    for cell in ws[row_number]:
        cell.font = font
        cell.border = border
        cell.alignment = left if cell.column in (1, 3) else center


def _number_or_empty(value):
    if value is None:
        return ''
    if value == 0:
        return ''
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value

    wb.save(filepath)
