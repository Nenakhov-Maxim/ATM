from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from login.models import User
from .models import *


admin.site.register(Tasks)
admin.site.register(Workplace)
admin.site.register(Profile_type)
admin.site.register(Task_status)
# admin.site.register(Users)
admin.site.register(Positions)
admin.site.register(Access_app)
admin.site.register(MasterTypeProblem)

@admin.register(Task_history)
class ProfileAdmin(admin.ModelAdmin):
    pass


