from django.db import models
from users.models import User

class SalaryStructure(models.Model):
    user              = models.OneToOneField(User, on_delete=models.CASCADE, related_name='salary')
    basic             = models.DecimalField(max_digits=12, decimal_places=2)
    hra               = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transport         = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medical           = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_allowances  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pf_deduction      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_deduction     = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    effective_from    = models.DateField()

    @property
    def gross(self): return self.basic + self.hra + self.transport + self.medical + self.other_allowances
    @property
    def net(self): return self.gross - self.pf_deduction - self.tax_deduction - self.other_deductions

    class Meta: db_table = 'salary_structure'


class Payslip(models.Model):
    user             = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payslips')
    month            = models.IntegerField()
    year             = models.IntegerField()
    basic            = models.DecimalField(max_digits=12, decimal_places=2)
    gross            = models.DecimalField(max_digits=12, decimal_places=2)
    deductions       = models.DecimalField(max_digits=12, decimal_places=2)
    net              = models.DecimalField(max_digits=12, decimal_places=2)
    days_worked      = models.IntegerField()
    generated_on     = models.DateTimeField(auto_now_add=True)
    paid             = models.BooleanField(default=False)

    class Meta:
        db_table = 'payslips'
        unique_together = ['user','month','year']

    def __str__(self): return f"Payslip – {self.user.full_name} – {self.month}/{self.year}"
