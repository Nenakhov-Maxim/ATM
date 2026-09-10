from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from master.shift_selection import reset_login_shift


@receiver(user_logged_in, dispatch_uid='production_shift_on_login')
def select_login_shift(sender, request, **kwargs):
    if request is not None:
        reset_login_shift(request.session)
