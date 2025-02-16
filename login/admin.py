from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import Group
from django.contrib import admin
from .models import User
from django.contrib.auth.admin import UserAdmin as OrigUserAdmin





class AuthorAdmin(OrigUserAdmin):
    list_display = (
        'username', 'id', 'first_name', 'last_name', 'email', 'position', 'production_area_id',
    )
    list_display_links = ('username', 'position', 'production_area_id')
    
    fieldsets = (
        (None, {
            'fields': ('username', 'first_name', 'last_name', 'email', 'position', 'production_area_id', 'password', 'groups', 'user_permissions', )
        }),
        # ('Advanced options', {
        #     'classes': ('collapse',),
        #     'fields': ('first_name', 'last_name'),
        # }),
    )
    list_filter = ('email', 'is_staff', 'is_active',)
    filter_horizontal = ('groups', 'user_permissions',)
 
admin.site.register(User, AuthorAdmin)

