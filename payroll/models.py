from django.db import models
from users.models import User

MONTH_NAMES = [
    '', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]

class SalaryStructure(models.Model):
    user             = models.OneToOneField(User, on_delete=models.CASCADE, related_name='salary')
    basic            = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    hra              = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transport        = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medical          = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pf_deduction     = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_deduction    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    effective_from   = models.DateField()

    @property
    def gross(self):
        return (float(self.basic) + float(self.hra) + float(self.transport) +
                float(self.medical) + float(self.other_allowances))

    @property
    def net(self):
        return self.gross - float(self.pf_deduction) - float(self.tax_deduction) - float(self.other_deductions)

    class Meta:
        db_table = 'salary_structure'

    def __str__(self):
        return f"{self.user.full_name} – ₹{self.net}"


class Payslip(models.Model):
    user             = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payslips')
    month            = models.IntegerField()
    year             = models.IntegerField()
    basic            = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    hra              = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transport        = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medical          = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pf_deduction     = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_deduction    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross            = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deductions       = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net              = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    days_worked      = models.IntegerField(default=22)
    generated_on     = models.DateTimeField(auto_now_add=True)
    paid             = models.BooleanField(default=False)

    class Meta:
        db_table = 'payslips'
        ordering = ['-year', '-month']

    def __str__(self):
        return f"Payslip – {self.user.full_name} – {self.month}/{self.year}"

    def get_month_display(self):
        try:
            return MONTH_NAMES[int(self.month)]
        except (IndexError, ValueError):
            return str(self.month)