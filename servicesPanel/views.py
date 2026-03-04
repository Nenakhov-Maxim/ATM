from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def services_panel_home(request):
    # Worker should not use services panel and must always land on worker app.
    perms = request.user.get_group_permissions()
    has_worker_perm = 'worker.change_workertypeproblem' in perms
    has_master_perms = any(perm.startswith('master.') for perm in perms)
    is_admin = request.user.is_superuser or request.user.is_staff
    is_master = has_master_perms and not is_admin
    is_worker_only = has_worker_perm and not has_master_perms and not is_admin
    if is_worker_only:
        return redirect('worker')
    context = {
        'is_admin': is_admin,
        'is_master': is_master,
    }
    return render(request, 'services_panel.html', context)
