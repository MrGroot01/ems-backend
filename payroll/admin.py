from django.contrib import admin
from .models import SalaryStructure, Payslip

@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display   = ('user', 'basic', 'hra', 'transport', 'pf_deduction', 'tax_deduction', 'effective_from')
    search_fields  = ('user__full_name', 'user__email', 'user__employee_id')
    ordering       = ('user__full_name',)
    raw_id_fields  = ('user',)

@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display   = ('user', 'month', 'year', 'basic', 'gross', 'net', 'days_worked', 'paid', 'generated_on')
    list_filter    = ('paid', 'year', 'month')
    search_fields  = ('user__full_name', 'user__email', 'user__employee_id')
    ordering       = ('-year', '-month')
    readonly_fields = ('generated_on',)
    raw_id_fields  = ('user',)
    actions        = ['mark_paid']

    @admin.action(description='Mark selected payslips as paid')
    def mark_paid(self, request, queryset):
        queryset.update(paid=True)