from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display   = ('email', 'full_name', 'employee_id', 'department', 'role', 'is_staff', 'is_active', 'face_registered')
    list_filter    = ('role', 'department', 'is_staff', 'is_active', 'face_registered')
    search_fields  = ('email', 'full_name', 'employee_id', 'phone')
    ordering       = ('full_name',)
    readonly_fields = ('date_joined',)

    fieldsets = (
        (None,              {'fields': ('email', 'password')}),
        ('Personal Info',   {'fields': ('full_name', 'employee_id', 'phone', 'department', 'role', 'profile_image')}),
        ('Face Recognition',{'fields': ('face_registered', 'face_encoding', 'face_image')}),
        ('OTP',             {'fields': ('otp', 'otp_created')}),
        ('Permissions',     {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates',           {'fields': ('date_joined',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'employee_id', 'department', 'role', 'password1', 'password2'),
        }),
    )