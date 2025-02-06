from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Profile, Task
from .forms import RegistrationForm, AssignTaskForm

from django.core.paginator import Paginator


from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage

# User Logout
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')


# User Registration
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            confirm_password = form.cleaned_data['confirm_password']

            # Validate password confirmation
            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return render(request, 'users/register.html', {'form': form})

            # Check if username is taken
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username is already taken. Please choose another.")
                return render(request, 'users/register.html', {'form': form})

            # Check if email is already registered
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email is already registered. Please use another.")
                return render(request, 'users/register.html', {'form': form})

            # Create a new user
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()

            # Create a profile for the user
            Profile.objects.create(user=user, role='executive')  # Default role

            # Auto-login after successful registration
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, "Registration successful! You are now logged in.")
                return redirect('main')

    else:
        form = RegistrationForm()

    return render(request, 'users/register.html', {'form': form})


# User Login
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, "Username and password are required.")
        elif form.is_valid():
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('main')
            else:
                messages.error(request, "Invalid username or password. Please try again.")
        else:
            messages.error(request, "Login failed. Please check your credentials.")

    else:
        form = AuthenticationForm()

    return render(request, 'users/login.html', {'form': form})


# Assign a Task (Admins & Managers Can Assign Tasks)
@login_required
def assign_task(request, user_id=None):
    if request.user.profile.role not in ['admin', 'manager']:
        messages.error(request, "You do not have permission to assign tasks.")
        return redirect('dashboard')

    user = get_object_or_404(User, id=user_id) if user_id else None
    tasks = Task.objects.filter(assigned_to=user) if user else Task.objects.all()

    if request.method == 'POST':
        form = AssignTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            if user:
                task.assigned_to = user
            task.assigned_by = request.user
            task.save()
            messages.success(request, f"Task assigned to {task.assigned_to.username} successfully!")
            return redirect('task_list')

    else:
        form = AssignTaskForm()

    # Allow only admins & managers to assign tasks to managers & executives
    users = User.objects.filter(profile__role__in=['manager', 'executive'])

    return render(request, 'users/assign_task.html', {
        'form': form,
        'users': users,
        'tasks': tasks,
        'user': user
    })


# List All Tasks
@login_required
def task_list(request):
    tasks = Task.objects.all()
    return render(request, 'users/task_list.html', {'tasks': tasks})


# Redirect Users Based on Their Role
@login_required
def main_page(request):
    profile, created = Profile.objects.get_or_create(user=request.user, defaults={'role': 'executive'})

    role_redirects = {
        'admin': 'admin_dashboard',
        'manager': 'manager_dashboard',
        'executive': 'executive_dashboard',
    }
    return redirect(role_redirects.get(profile.role, 'login'))


# Universal Dashboard Redirector
@login_required
def dashboard(request):
    profile = get_object_or_404(Profile, user=request.user)

    if profile.role == 'admin':
        return redirect('admin_dashboard')
    elif profile.role == 'manager':
        return redirect('manager_dashboard')
    elif profile.role == 'executive':
        return redirect('executive_dashboard')

    return redirect('login')


# Admin Dashboard (Now Can Assign Tasks)



@login_required
def admin_dashboard(request):
    """Admin can view users and assign tasks with pagination."""
    
    if request.user.profile.role != 'admin':
        messages.error(request, "You are not authorized to view this page.")
        return redirect('dashboard')

    users_list = Profile.objects.all()  # Get all users
    paginator = Paginator(users_list, 5)  # Show 5 users per page

    page_number = request.GET.get('page')  # Get current page number from request
    users = paginator.get_page(page_number)  # Get users for the requested page

    form = AssignTaskForm()  # Task assignment form

    return render(request, 'users/admin_dashboard.html', {
        'users': users,
        'form': form
    })

#manager
@login_required
def manager_dashboard(request):
    """Managers (and Admins) can view executives with pagination and upload task files."""

    # Ensure only admins and managers can access this page
    if request.user.profile.role not in ['admin', 'manager']:
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    # Fetch tasks assigned to the manager by an admin
    tasks_assigned_to_manager = Task.objects.filter(assigned_to=request.user, assigned_by__profile__role='admin')

    # Handle task file upload
    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        uploaded_file = request.FILES.get('file_upload')

        if task_id and uploaded_file:
            task = get_object_or_404(Task, id=task_id)
            task.file_upload = uploaded_file
            task.completed = True  # Mark task as completed after upload
            task.save()
            messages.success(request, "File uploaded successfully! Task marked as completed.")
        return redirect('manager_dashboard')

    # Fetch executives under this manager (paginated)
    executives_list = Profile.objects.filter(role='executive')
    paginator = Paginator(executives_list, 5)  # 5 executives per page
    page_number = request.GET.get('page')
    executives = paginator.get_page(page_number)

    return render(request, 'users/manager_dashboard.html', {
        'tasks_assigned_to_manager': tasks_assigned_to_manager,
        'executives': executives
    })




# Executive Dashboard (View Assigned Tasks

@login_required
def executive_dashboard(request):
    """Executive can view assigned tasks with pagination."""

    tasks_list = Task.objects.filter(assigned_to=request.user)  # Fetch only tasks assigned to the logged-in executive
    paginator = Paginator(tasks_list, 5)  # Show 5 tasks per page

    page_number = request.GET.get('page')  # Get current page number from request
    tasks = paginator.get_page(page_number)  # Get tasks for the requested page

    return render(request, 'users/executive_dashboard.html', {'tasks': tasks})



@login_required
def submit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == 'POST' and request.FILES.get('upload_file'):
        uploaded_file = request.FILES['upload_file']
        task.upload_file = uploaded_file
        task.completed = True  # Mark task as completed
        task.save()
        return redirect('executive_dashboard')

    return HttpResponse("Invalid submission", status=400)


# Update User Role (Only Admins Can Change User Roles)

@login_required
@require_POST
def update_role(request, user_id):
    # Ensure only admins can change roles
    if request.user.profile.role != 'admin':
        messages.error(request, "You are not authorized to change roles.")
        return redirect('dashboard')

    user = get_object_or_404(User, pk=user_id)
    role = request.POST.get('role')

    # Check if the role is one of the allowed options
    if role in ['admin', 'manager', 'executive']:
        # Ensure Profile exists or create one
        profile, created = Profile.objects.get_or_create(user=user)

        # Update the role
        profile.role = role
        profile.save()

        # Success message
        messages.success(request, f"Role updated successfully to {role.capitalize()}.")

    else:
        # Error message in case the role is not valid
        messages.error(request, "Invalid role selection.")

    # Redirect to the dashboard or relevant page
    return redirect('dashboard')
