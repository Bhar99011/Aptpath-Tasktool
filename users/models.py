from django.db import models
from django.contrib.auth.models import User

class Task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)  # Due date for task
    completed = models.BooleanField(default=False)
    upload_file = models.FileField(upload_to='task_uploads/', null=True, blank=True)  # File upload field

    def mark_completed(self):
        """Mark the task as completed when a file is uploaded."""
        if self.upload_file:
            self.completed = True
            self.save()

    def has_submission(self):
        """Check if a task has an uploaded file."""
        return bool(self.upload_file)

    def __str__(self):
        return f"{self.title} (Assigned to: {self.assigned_to.username if self.assigned_to else 'Unassigned'})"


class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('executive', 'Executive'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='executive')

    def __str__(self):
        return f"{self.user.username} - {self.role}"
