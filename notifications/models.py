from django.db import models
from users.models import User

class Notification(models.Model):
    TYPES = [
        ('info',         'Info'),
        ('success',      'Success'),
        ('warning',      'Warning'),
        ('leave',        'Leave'),
        ('task',         'Task'),
        ('payroll',      'Payroll'),
        ('announcement', 'Announcement'),
    ]

    user       = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='notifications')
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    type       = models.CharField(max_length=20, choices=TYPES, default='info')
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} — {self.title}"