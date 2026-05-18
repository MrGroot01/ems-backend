from django.db import models
from users.models import User


class Employee(models.Model):
    DEPT   = [('engineering','Engineering'),('hr','HR'),('finance','Finance'),
              ('marketing','Marketing'),('operations','Operations'),('design','Design'),('sales','Sales')]
    STATUS = [('active','Active'),('inactive','Inactive'),('on_leave','On Leave')]

    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    designation = models.CharField(max_length=100)
    department  = models.CharField(max_length=50, choices=DEPT)
    date_joined = models.DateField()
    date_of_birth = models.DateField(null=True, blank=True)
    address     = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    status      = models.CharField(max_length=20, choices=STATUS, default='active')
    manager     = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employees'

    def __str__(self):
        return f"{self.user.full_name} – {self.designation}"
