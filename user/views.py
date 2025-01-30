from django.contrib.auth.hashers import check_password,make_password
from django.shortcuts import render, redirect, get_object_or_404
from user.models import User, Role, Task
from django.contrib import messages
from django.contrib.auth import authenticate
from django.core.paginator import Paginator


def validate_password(password):
    import re
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return "Password must include at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return "Password must include at least one lowercase letter."
    if not re.search(r'[0-9]', password):
        return "Password must include at least one number."
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
        return "Password must include at least one special character."
    return None


def signup_fun(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        error = None

        # Check username
        if not username.isalpha():
            error = "Username must only contain letters."
        elif User.objects.filter(username__iexact=username).exists():
            error = "Username already exists."

        # Check email
        elif User.objects.filter(email=email).exists():
            error = "Email is already registered."

        # Validate password
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            error = validate_password(password)

        if error:
            return render(request, "signup.html", {"error": error})

        #update_fields=['role']
        # Assign default role (User) during signup
        user_role = Role.objects.get(name="User")  # Ensure the 'User' role exists in your DB
        User.objects.create(username=username, email=email, password=make_password(password), role=user_role)
        return redirect('login')

    return render(request, 'signup.html')


def login_fun(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']

        try:
            # Fetch the user by email
            user = User.objects.get(email=email)
            print(f"Entered password: {password}")
            print(f"Stored hashed password: {user.password}")
            check_result = check_password(password, user.password)
            print(f"check_password result: {check_result}")
            print(f"{user.username}----{password}-----{user.password}")
            # Check if the provided password matches
            if check_password(password, user.password):
                # Set the user session
                request.session['user_id'] = user.id
                request.session['role'] = user.role.name
                messages.success(request, "Successfully logged in")
                # Authentication successful
                # Redirect based on user role
                if user.role.name == 'Admin':
                    return redirect('admin_dash')  # Redirect to admin dashboard
                elif user.role.name == 'Manager':
                    return redirect('manager_dash')  # Redirect to manager dashboard
                elif user.role.name == 'User':
                    return redirect('user_dash')  # Redirect to user dashboard
                else:
                    print(f"Invalid")
                    return render(request, 'login.html', {'message': 'Invalid role configuration.'})
            else:
                print(f"Invalidd")
                # Authentication failed
                return render(request,'login.html',{"error": "Invalid username or password"})

        except User.DoesNotExist:
            error = "Invalid credentials."

        return render(request, "login.html", {"error": error})

    return render(request, "login.html")



def logout(request):
    request.session.flush()  # Clear session
    return redirect('login')

from django.core.paginator import Paginator

def admin_dash_func(request):
    # Ensure the user is logged in
    if 'user_id' not in request.session:
        return redirect('login')

    user = get_object_or_404(User, id=request.session['user_id'])

    # Check if the logged-in user has Admin role
    if user.role.name != 'Admin':
        return redirect('login')

    # Handle actions for Admin
    users = User.objects.all()
    tasks = Task.objects.all()

    # Pagination setup
    paginator = Paginator(tasks, 2)  # Show 2 tasks per page
    page_number = request.GET.get('page')  # Get current page number from query parameters
    tasks_page = paginator.get_page(page_number)

    if request.method == "POST":
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')

        if action == "update_role":
            user_to_update = User.objects.filter(id=user_id).first()
            if not user_to_update:
                messages.error(request, "User not found.")
                return redirect('admin_dash')

            new_role_name = request.POST.get('role')
            new_role = Role.objects.get(name=new_role_name)

            user_to_update.role = new_role
            user_to_update.save(update_fields=['role'])

            if user_to_update.id == request.session['user_id']:
                request.session['role'] = new_role.name
                request.session.modified = True
                messages.success(request, f"Your role has been updated to '{new_role_name}'.")

            messages.success(request, f"User's role has been updated to '{new_role_name}'.")
            return redirect('admin_dash')

        elif action == "assign_task":
            task_title = request.POST.get('task_title')
            task_desc = request.POST.get('description')
            assigned_to_id = request.POST.get('user_id')
            assigned_to = get_object_or_404(User, id=assigned_to_id)

            Task.objects.create(
                title=task_title,
                description=task_desc,
                assigned_to=assigned_to,
                assigned_by=user,
            )
            messages.success(request, f"Task '{task_title}' has been successfully updated.")
            return redirect('admin_dash')

        elif action == "add_user":
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password']
            role = request.POST.get('role')
            role_to_assign = Role.objects.get(name=role)
            User.objects.create(username=username, email=email, password=make_password(password), role=role_to_assign)
            messages.success(request, f"User '{username}' has been successfully added.")
            return redirect('admin_dash')

        elif action == "delete_task":
            Task.objects.filter(id=request.POST.get('task_id')).delete()
            messages.success(request, "Task has been successfully deleted.")
            return redirect('admin_dash')

        elif action == "update_task":
            task_id = request.POST.get("task_id")
            task_title = request.POST.get("task_title")
            task_desc = request.POST.get('description')
            assigned_to_id = request.POST.get("assigned_to")

            try:
                task = get_object_or_404(Task, id=task_id)
                assigned_to = get_object_or_404(User, id=assigned_to_id)

                task.title = task_title
                task.description = task_desc
                task.assigned_to = assigned_to
                task.save()

                messages.success(request, f"Task '{task_title}' has been successfully updated.")
            except Exception as e:
                messages.error(request, f"An error occurred while updating the task: {str(e)}")

        elif action == "delete_user":
            User.objects.filter(id=user_id).delete()
            messages.success(request, "User has been successfully deleted.")
            return redirect('admin_dash')

    roles = Role.objects.all()

    return render(request, 'admin_dashboard.html', {
        'users': users,
        'tasks': tasks_page,  # Pass the paginated tasks
        'roles': roles
    })

def manager_dash_func(request):
    if 'user_id' not in request.session:
        return redirect('login')

    manager = get_object_or_404(User, id=request.session['user_id'])
    if manager.role.name != 'Manager':
        return redirect('login')

    # Handle actions for Manager
    users = User.objects.filter(role__name__in=["User"])
    tasks = Task.objects.filter(assigned_to__role__name="User")

    if request.method == "POST":
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        user = User.objects.filter(id=user_id)

        if action == "update_task":
            task_id = request.POST.get("task_id")
            task_desc = request.POST.get('description')
            task_title = request.POST.get("task_title")
            assigned_to_id = request.POST.get("assigned_to")

            try:
                # Fetch the task and assigned user
                task = get_object_or_404(Task, id=task_id)
                assigned_to = get_object_or_404(User, id=assigned_to_id)

                # Update task details
                task.title = task_title
                task.description = task_desc
                task.assigned_to = assigned_to
                task.save()

                messages.success(request, f"Task '{task_title}' has been successfully updated.")
            except Exception as e:
                messages.error(request, f"An error occurred while updating the task: {str(e)}")

        elif action == "update_user":
            return render(request, 'update.html',{'user':user})

        elif action == "delete_task":
            Task.objects.filter(id=request.POST.get('task_id')).delete()

        elif action == "delete_user":
            User.objects.filter(id=user_id).delete()

    return render(request, 'manager_dashboard.html', {'users': users, 'tasks': tasks})


def user_dash_func(request):
    if 'user_id' not in request.session:
        return redirect('login')

    user = get_object_or_404(User, id=request.session['user_id'])
    if user.role.name != 'User':
        return redirect('login')

    # Fetch tasks assigned to the logged-in user
    tasks = Task.objects.filter(assigned_to=user)
    return render(request, 'user_dashboard.html', {'tasks': tasks, 'user': user})
