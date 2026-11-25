"""Area permissions for the master's interface; worker line access is separate."""
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404

from login.models import ProductionArea, Workplace
from .models import Tasks


def area_ids_for(user):
    return set(available_areas(user).values_list('pk', flat=True))


def available_areas(user):
    if not user or not user.is_authenticated or not user.pk:
        return ProductionArea.objects.none()
    return ProductionArea.objects.filter(
        Q(managers=user) | Q(pk=user.production_area_id_id),
    ).distinct().order_by('production_area_name', 'pk')


def selected_area(user, value):
    if value in (None, ''):
        return None
    try:
        area_id = int(value)
    except (ValueError, TypeError):
        raise PermissionDenied('Недоступный участок')
    if area_id not in area_ids_for(user):
        raise PermissionDenied('Недоступный участок')
    return area_id


def task_area_query(user, area_id=None):
    areas = available_areas(user)
    if area_id is not None:
        areas = areas.filter(pk=area_id)
    ids = areas.values('pk')
    # A current workplace is authoritative; legacy tasks without one use their saved area.
    return Q(task_workplace__production_area_id__in=ids) | Q(
        task_workplace__isnull=True, production_area_id__in=ids,
    )


def available_workplaces(user):
    return Workplace.objects.filter(production_area_id__in=available_areas(user).values('pk')).select_related('production_area_id').order_by('production_area_id__production_area_name', 'workplace_name', 'pk')


def accessible_task(user, task_id):
    try:
        task_id = int(task_id)
    except (ValueError, TypeError):
        from django.http import Http404
        raise Http404('Задание не найдено')
    return get_object_or_404(Tasks.objects.filter(task_area_query(user)), pk=task_id)
