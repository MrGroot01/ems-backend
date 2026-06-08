from django.db import models
from users.models import User

class Attendance(models.Model):
    STATUS = [
        ('present',  'Present'),
        ('absent',   'Absent'),
        ('half_day', 'Half Day'),
        ('late',     'Late'),
        ('wfh',      'Work From Home'),
    ]

    ATTENDANCE_TYPE = [
        ('manual',    'Manual'),
        ('face_scan', 'Face Scan'),
    ]

    user             = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance')
    date             = models.DateField()
    check_in         = models.TimeField(null=True, blank=True)
    check_out        = models.TimeField(null=True, blank=True)
    status           = models.CharField(max_length=20, choices=STATUS, default='present')
    working_hours    = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes            = models.TextField(blank=True)
    attendance_type  = models.CharField(max_length=20, choices=ATTENDANCE_TYPE, default='manual')  # ← NEW
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table     = 'attendance'
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.full_name} – {self.date} – {self.status}"