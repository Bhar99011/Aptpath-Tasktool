from django.contrib import messages
from apt_app.models import users_details

def username_validation(request, user_name):
    if users_details.objects.filter(user_name=user_name).exists():
        messages.error(request, "User Name already exists!")
        return False
    return True

def email_validation (request,email):
    if '@' in email and '.' in email:
        return True
    else:
        messages.error(request,'Check Your Email id!')
        return False


def password_validation (request,password,confirm_password):
    if len(password)<8:
        messages.error(request,'Password Must have 8 digits ')
        return False
    elif password == confirm_password:
        return True
    else:
       messages.error(request,"Password should be match! ")
       return False
       






