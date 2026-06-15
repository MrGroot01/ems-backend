from django.contrib import admin
from .models import Course, CourseEnrollment

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display   = ('title', 'department', 'difficulty', 'duration_hrs', 'is_active', 'created_by', 'created_at')
    list_filter    = ('department', 'difficulty', 'is_active')
    search_fields  = ('title', 'description', 'department')
    ordering       = ('department', 'title')
    readonly_fields = ('created_at',)
    raw_id_fields  = ('created_by',)

@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display   = ('user', 'course', 'status', 'progress', 'quiz_score', 'quiz_passed', 'enrolled_at', 'completed_at')
    list_filter    = ('status', 'quiz_passed', 'course__department')
    search_fields  = ('user__full_name', 'user__email', 'course__title')
    ordering       = ('-enrolled_at',)
    readonly_fields = ('enrolled_at', 'completed_at', 'certificate_id')
    raw_id_fields  = ('user', 'course')