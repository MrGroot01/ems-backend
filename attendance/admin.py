from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display   = ('user', 'date', 'status', 'check_in', 'check_out', 'working_hours', 'attendance_type')
    list_filter    = ('status', 'attendance_type', 'date')
    search_fields  = ('user__full_name', 'user__email', 'user__employee_id')
    ordering       = ('-date',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at',)
    raw_id_fields  = ('user',)