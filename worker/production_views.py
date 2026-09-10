import json

from django import forms
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from master.databaseWork import DatabaseWork
from master.models import Tasks
from master.production import ProductionConflict, change_coating, decide_stock, finish_task, hand_over_task
from .line_access import authorized_line_id


class CounterForm(forms.Form):
    id_task = forms.IntegerField(min_value=1)
    total = forms.IntegerField(min_value=0)
    expected_total = forms.IntegerField(min_value=0)
    revision = forms.IntegerField(min_value=0)


class CoatingForm(CounterForm):
    coating = forms.CharField(max_length=100)


class StockForm(forms.Form):
    id_task = forms.IntegerField(min_value=1)
    decision = forms.ChoiceField(choices=[('yes', 'Да'), ('no', 'Нет')])
    length = forms.FloatField(required=False, min_value=0.001)


def payload(request):
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def state(task):
    return dict(
        id_task=task.pk, total=task.profile_amount_now, revision=task.coating_revision,
        coating=task.task_coating_thickness or '', stock=bool(task.stock_source_id),
        pending_stock=task.allow_stock and not task.stock_source_id and task.stock_decision is None and task.task_status_id == 2,
        profile=str(task.task_profile_type), length=task.task_profile_length,
    )


@login_required
@permission_required('worker.change_workertypeproblem', raise_exception=True)
@require_GET
def production_state(request):
    try:
        task = Tasks.objects.select_related('task_profile_type').get(
            pk=request.GET.get('id_task'), task_workplace_id=authorized_line_id(request),
        )
    except (Tasks.DoesNotExist, ValueError):
        return JsonResponse({'message': 'Задание не найдено.'}, status=404)
    return JsonResponse(state(task))


def counter_action(request, form_class, action):
    form = form_class(payload(request))
    if not form.is_valid():
        return JsonResponse({'message': 'Проверьте поля формы.', 'errors': form.errors}, status=400)
    data = form.cleaned_data
    task_id = data.pop('id_task')
    try:
        task = action(task_id, authorized_line_id(request), request.user, **data)
    except Tasks.DoesNotExist:
        return JsonResponse({'message': 'Задание не найдено.'}, status=404)
    except ProductionConflict as error:
        return JsonResponse({'message': str(error)}, status=409)
    except ValueError as error:
        return JsonResponse({'message': str(error)}, status=400)
    return task


@login_required
@permission_required('worker.change_workertypeproblem', raise_exception=True)
@require_POST
def update_coating(request):
    result = counter_action(request, CoatingForm, change_coating)
    return result if isinstance(result, JsonResponse) else JsonResponse(state(result))


@login_required
@permission_required('worker.change_workertypeproblem', raise_exception=True)
@require_POST
def complete_production(request):
    result = counter_action(request, CounterForm, finish_task)
    if isinstance(result, JsonResponse):
        return result
    DatabaseWork({}).add_data_to_user_analytics(request.user.pk, result.pk)
    return JsonResponse(state(result))


@login_required
@permission_required('worker.change_workertypeproblem', raise_exception=True)
@require_POST
def handover_production(request):
    result = counter_action(request, CounterForm, hand_over_task)
    return result if isinstance(result, JsonResponse) else JsonResponse(state(result))


@login_required
@permission_required('worker.change_workertypeproblem', raise_exception=True)
@require_POST
def stock_decision(request):
    form = StockForm(payload(request))
    if not form.is_valid():
        return JsonResponse({'message': 'Проверьте длину профиля и решение.'}, status=400)
    data = form.cleaned_data
    try:
        task = decide_stock(data['id_task'], authorized_line_id(request), request.user, data['decision'] == 'yes', data['length'])
    except Tasks.DoesNotExist:
        return JsonResponse({'message': 'Задание не найдено.'}, status=404)
    except (ProductionConflict, ValueError) as error:
        return JsonResponse({'message': str(error)}, status=409)
    return JsonResponse({'success': True, 'task_id': task.pk if task else None})
