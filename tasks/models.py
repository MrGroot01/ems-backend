from django.db import models
from users.models import User


class Task(models.Model):
    PRIORITY = [('low','Low'),('medium','Medium'),('high','High'),('urgent','Urgent')]
    STATUS   = [('todo','Pending'),('in_progress','In Progress'),('completed','Completed')]

    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks')
    priority    = models.CharField(max_length=8,  choices=PRIORITY, default='medium')
    status      = models.CharField(max_length=12, choices=STATUS,   default='todo')
    progress    = models.IntegerField(default=0)
    due_date    = models.DateField()
    completed_at= models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tasks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} → {self.assigned_to.full_name}"
