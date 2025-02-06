from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Task
import datetime
import re

class AssignTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'due_date']
        widgets = {
            'due_date': forms.SelectDateWidget(years=range(datetime.date.today().year, datetime.date.today().year + 10)),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter task description'}),
            'title': forms.TextInput(attrs={'placeholder': 'Enter task title'}),
            'assigned_to': forms.Select(attrs={'class': 'assigned-to-dropdown'}),
        }

    def __init__(self, *args, **kwargs):
        """Filter assigned_to field to show only managers & executives."""
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(profile__role__in=['manager', 'executive'])

    def clean_due_date(self):
        """Ensure that the due date is not in the past."""
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < datetime.date.today():
            raise ValidationError("The due date cannot be in the past.")
        return due_date



class SubmitTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['upload_file']


class RegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter username'}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter email address'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
        required=True,
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        required=True,
    )

    def clean_username(self):
        """Ensure the username is unique and contains only valid characters."""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("Username can only contain letters, numbers, and underscores.")

        return username

    def clean_email(self):
        """Ensure email is unique and properly formatted."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered. Please use another.")

        # Ensure the email format is valid
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            raise ValidationError("Please enter a valid email address.")

        return email

    def clean(self):
        """Perform password validation and ensure passwords match."""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        # Check if passwords match
        if password != confirm_password:
            raise ValidationError("Passwords do not match.")

        # Password complexity validation
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not any(char.isupper() for char in password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not any(char.islower() for char in password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password must contain at least one digit.")
        if not any(char in "!@#$%^&*()-_+=<>?/{}[]" for char in password):
            raise ValidationError("Password must contain at least one special character (!@#$%^&*()-_+=<>?/{}[]).")

        return cleaned_data
