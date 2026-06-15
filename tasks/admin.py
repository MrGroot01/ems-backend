from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display   = ('title', 'assigned_to', 'assigned_by', 'priority', 'status', 'progress', 'due_date')
    list_filter    = ('status', 'priority')
    search_fields  = ('title', 'assigned_to__full_name', 'assigned_by__full_name')
    ordering       = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    raw_id_fields  = ('assigned_to', 'assigned_by')

    fieldsets = (
        ('Task Info',  {'fields': ('title', 'description', 'assigned_to', 'assigned_by')}),
        ('Status',     {'fields': ('priority', 'status', 'progress', 'due_date', 'completed_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )