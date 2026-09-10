from django.core.exceptions import PermissionDenied
from login.models import Workplace


def worker_line_id(request):
    addresses = {f'192.168.211.{10 + i}': i + 1 for i in range(6)}
    return addresses.get(request.META.get('REMOTE_ADDR'), 1)


def authorized_line_id(request):
    line_id = worker_line_id(request)
    if not request.user.is_superuser:
        area = request.user.production_area_id_id
        if not area or not Workplace.objects.filter(pk=line_id, production_area_id_id=area).exists():
            raise PermissionDenied
    return line_id
