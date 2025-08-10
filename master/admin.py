from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from login.models import User
from .models import *


admin.site.register(Tasks)
admin.site.register(Workplace)
admin.site.register(ProfileType)
admin.site.register(TaskStatus)
# admin.site.register(Users)
admin.site.register(Positions)
admin.site.register(AccessApp)
admin.site.register(MasterTypeProblem)

@admin.register(TaskHistory)
class ProfileAdmin(admin.ModelAdmin):
    pass


