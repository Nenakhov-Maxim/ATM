from django.core.exceptions import PermissionDenied
from login.models import Workplace


LINE_ADDRESSES = {f'192.168.211.{10 + i}': i + 1 for i in range(10)}


def worker_line_id(request):
    return LINE_ADDRESSES.get(request.META.get('REMOTE_ADDR'), 1)


def authorized_line_id(request):
    line_id = worker_line_id(request)
    if not request.user.is_superuser:
        area = request.user.production_area_id_id
        if not area or not Workplace.objects.filter(pk=line_id, production_area_id_id=area).exists():
            raise PermissionDenied
    return line_id
