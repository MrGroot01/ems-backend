from django.contrib import admin
from .models import Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display   = ('user', 'designation', 'department', 'status', 'date_joined', 'manager')
    list_filter    = ('department', 'status')
    search_fields  = ('user__full_name', 'user__email', 'user__employee_id', 'designation')
    ordering       = ('user__full_name',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields  = ('user', 'manager')

    fieldsets = (
        ('Employee Info',   {'fields': ('user', 'designation', 'department', 'status', 'manager')}),
        ('Personal',        {'fields': ('date_joined', 'date_of_birth', 'address', 'emergency_contact')}),
        ('Timestamps',      {'fields': ('created_at', 'updated_at')}),
    )