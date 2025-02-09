from django.db import models
from django.contrib.auth.hashers import make_password


class Role(models.Model):

    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class User(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=256)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)


    def save(self, *args, **kwargs):
          # Hash the password before saving
        super().save(*args, **kwargs)


class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks')
    created_at = models.DateTimeField(auto_now_add=True)  # Add Timestamp
    status = models.CharField(
        max_length=10,
        choices=[("Pending", "Pending"), ("Submitted", "Submitted")],
        default="Pending"
    )
    answer = models.TextField(blank=True, null=True)  # Answer submission field

    def __str__(self):
        return self.title
