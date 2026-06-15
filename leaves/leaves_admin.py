from django.contrib import admin
from .models import Leave

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display   = ('user', 'leave_type', 'start_date', 'end_date', 'days', 'status', 'approved_by', 'applied_on')
    list_filter    = ('status', 'leave_type')
    search_fields  = ('user__full_name', 'user__email', 'user__employee_id')
    ordering       = ('-applied_on',)
    readonly_fields = ('applied_on', 'updated_at', 'days')
    raw_id_fields  = ('user', 'approved_by')

    fieldsets = (
        ('Leave Details', {'fields': ('user', 'leave_type', 'start_date', 'end_date', 'days', 'reason')}),
        ('Approval',      {'fields': ('status', 'approved_by', 'reject_reason')}),
        ('Timestamps',    {'fields': ('applied_on', 'updated_at')}),
    )