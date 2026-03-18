from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from login.models import User
from .models import *


@admin.register(Tasks)
class TasksAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'task_name',
        'task_user_created_by',
        'task_user_created',
        'task_status',
        'task_workplace',
        'created_at',
    )
    list_filter = ('task_status', 'task_workplace', 'task_user_created_by', 'production_area')
    search_fields = (
        'task_name',
        'task_user_created',
        'task_user_created_by__username',
        'task_user_created_by__first_name',
        'task_user_created_by__last_name',
    )
    autocomplete_fields = ('task_user_created_by',)
    readonly_fields = ('task_user_created',)


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


