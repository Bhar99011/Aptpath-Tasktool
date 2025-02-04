from django.db import models
# from django.contrib.auth.hashers import make_password
# Create your models here   


class users_details(models.Model):
    user_name=models.CharField(max_length=100)
    email=models.EmailField()
    password=models.CharField(max_length=200)
    role=models.CharField(max_length=50,default="user")

    def __str__(self):
        return self.user_name
class Tasks(models.Model):
    title=models.CharField(max_length=1000)
    description=models.TextField()
    assigned_to=models.ForeignKey(users_details,on_delete=models.CASCADE, related_name="assigned_to")
    assigned_by=models.ForeignKey(users_details,on_delete=models.CASCADE, related_name="assigned_by")
    created_at=models.DateField(auto_now=True)
    # def save(self,*args, **kwargs):
    #     if not self.password.startswith('pbkdf2_'):
    #         self.password=make_password(self.password)
    #     super().save(*args,**kwargs)




