from django.db import models
from users.models import User


class Leave(models.Model):
    TYPES  = [('sick','Sick'),('casual','Casual'),('annual','Annual'),('unpaid','Unpaid')]
    STATUS = [('pending','Pending'),('approved','Approved'),
              ('rejected','Rejected'),('cancelled','Cancelled')]

    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaves')
    leave_type    = models.CharField(max_length=10, choices=TYPES)
    start_date    = models.DateField()
    end_date      = models.DateField()
    days          = models.IntegerField(default=1)
    reason        = models.TextField()
    status        = models.CharField(max_length=12, choices=STATUS, default='pending')
    approved_by   = models.ForeignKey(User, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='approved_leaves')
    reject_reason = models.TextField(blank=True)
    applied_on    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leaves'
        ordering = ['-applied_on']

    def __str__(self):
        return f"{self.user.full_name} – {self.leave_type} ({self.status})"

    def save(self, *args, **kwargs):
        # Auto-calculate days
        if self.start_date and self.end_date:
            delta = (self.end_date - self.start_date).days + 1
            self.days = max(1, delta)
        super().save(*args, **kwargs)
