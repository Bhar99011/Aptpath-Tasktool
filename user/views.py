from django.contrib.auth.hashers import check_password,make_password
from django.shortcuts import render, redirect, get_object_or_404
from user.models import User, Role, Task
from django.contrib import messages
from django.contrib.auth import authenticate
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required


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
                # if user.role.name in ["Admin", "Manager", "User"]:
                return render(request, 'profile.html', {"user": user})  # Redirect to admin dashboard
                # elif user.role.name == 'Manager':
                #     return redirect('manager_dash')  # Redirect to manager dashboard
                # elif user.role.name == 'User':
                #     return redirect('user_dash')  # Redirect to user dashboard
                # else:
                #     print(f"Invalid")
                #     return render(request, 'login.html', {'message': 'Invalid role configuration.'})
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


def profile(request):
    user = get_object_or_404(User, id=request.session['user_id'])
    return render(request, "profile.html", {'user': user})


def tasks_view(request):

    users = User.objects.all()
    user = get_object_or_404(User, id=request.session['user_id'])

    # Get tasks assigned to the logged-in user
    assigned_to_me = Task.objects.filter(assigned_to=user).order_by("-created_at")

    # Get tasks assigned by the logged-in user
    assigned_by_me = Task.objects.filter(assigned_by=user).order_by("-created_at")

    if user.role.name == "Admin":
         all_tasks = Task.objects.all().order_by("-created_at")
    # Managers see tasks assigned by them and tasks assigned to Users
    elif user.role.name == "Manager":
        all_tasks = Task.objects.filter(assigned_to__role__name="User").order_by("-created_at")
    # Regular Users don't have an "All Tasks" section
    else:
        all_tasks = None

    # Pagination for "Tasks Assigned to Me"
    paginator_all = Paginator(all_tasks, 5) if all_tasks else None
    paginator_assigned_to_me = Paginator(assigned_to_me, 2)
    paginator_assigned_by_me = Paginator(assigned_by_me, 2)

    page_number = request.GET.get("page")
    paginated_all_tasks = paginator_all.get_page(page_number) if paginator_all else None
    paginated_assigned_to_me = paginator_assigned_to_me.get_page(page_number)
    paginated_assigned_by_me = paginator_assigned_by_me.get_page(page_number)

    # Fetch users for assignment dropdown
    if user.role.name == "Admin":
        users = User.objects.exclude(id=request.session['user_id'])  # Admins can assign tasks to anyone except themselves
    elif user.role.name == "Manager":
        users = User.objects.filter(role__name="User")  # Managers can only assign tasks to Users
    else:
        users = None  # Users cannot assign tasks

    # Handle task operations
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "assign_task":
            title = request.POST.get("title")
            description = request.POST.get("description")
            user_id = request.POST.get("user_id")

            if not title or not description or not user_id:
                messages.error(request, "All fields are required to assign a task.")
            else:
                assigned_user = get_object_or_404(User, id=int(user_id))

                # Admins can assign tasks to anyone except themselves
                if user.role.name == "Admin" or (user.role.name == "Manager" and assigned_user.role.name == "User") or (user.role.name == "User" and assigned_user == user):
                    Task.objects.create(
                        title=title,
                        description=description,
                        assigned_to=assigned_user,
                        assigned_by=user,
                    )
                    messages.success(request, "Task assigned successfully.")
                else:
                    messages.error(request, "You do not have permission to assign this task.")
            return redirect("task")

        elif action == "update_task":
            task_id = request.POST.get("task_id")
            task = get_object_or_404(Task, id=task_id)
            assigned_to = request.POST.get("assigned_to")
            assigned_user = get_object_or_404(User, id=assigned_to)

            if user.role.name in ["Admin", "Manager"] or task.assigned_by == user:
                task.title = request.POST.get("title")
                task.description = request.POST.get("description")
                task.assigned_to = assigned_user
                task.save()
                messages.success(request, "Task updated successfully.")

            else:
                messages.error(request, "You do not have permission to update this task.")

                # if new_assigned_to:
                #     assigned_user = get_object_or_404(User, id=new_assigned_to)
                #
                #     # Restrict reassigning tasks based on role
                #     if user.role.name == "Admin" and assigned_user.role.name in ["Admin", "Manager", "User"]:
                #         task.assigned_to = assigned_user
                #     elif user.role.name == "Manager" and assigned_user.role.name == "User":
                #         task.assigned_to = assigned_user
                #     else:
                #         messages.error(request, "Invalid assignment permissions.")
            return redirect("task")

        elif action == "delete_task":
            task_id = request.POST.get("task_id")
            task = get_object_or_404(Task, id=task_id)

            if user.role.name in ["Admin", "Manager"] or task.assigned_by == user:
                task.delete()
                messages.success(request, "Task deleted successfully.")
            else:
                messages.error(request, "You do not have permission to delete this task.")

            return redirect("task")
        elif action == "submit_answer":
            task_id = request.POST.get("task_id")
            task = get_object_or_404(Task, id=task_id)
            if task.assigned_to == user and task.status == "Pending":
                task.answer = request.POST.get("answer")
                task.status = "Submitted"
                task.save()
                messages.success(request, "Answer submitted successfully.")
            else:
                messages.error(request, "You cannot submit an answer for this task.")
            return redirect("task")

    return render(request, "tasks.html", {
        "all_tasks": paginated_all_tasks,
        "assigned_by_me": paginated_assigned_by_me,
        "assigned_to_me": paginated_assigned_to_me,
        "users": users,
        "user": user
    })


def users_view(request):
    user = get_object_or_404(User, id=request.session.get('user_id'))
    if user.role.name not in ["Admin", "Manager"]:
        messages.error(request, "You are not authorized to view this page.")
        return redirect("dashboard")

    if user.role.name == "Admin":
        users_list = User.objects.all()  # Admin can view all users
    else:  # If Manager
        users_list = User.objects.filter(role__name="User")  # Manager can view only Users
      # Fetch users
    paginator = Paginator(users_list, 5)  # Show 5 users per page

    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)

    roles = Role.objects.all() if user.role.name == "Admin" else Role.objects.filter(name="User")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_user" and user.role.name in ["Admin", "Manager"]:
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password']
            role = request.POST.get('role')
            role_to_assign = Role.objects.get(name=role)

            error = None
            if user.role.name == "Manager" and role != "User":
                messages.error(request, "Managers can only add Users.")
                return redirect("user")
            # Check username
            if not username.isalpha():
                error = "Username must only contain letters."
            elif User.objects.filter(username__iexact=username).exists():
                error = "Username already exists."
            # Check email
            elif User.objects.filter(email=email).exists():
                error = "Email is already registered."
            # Validate password
            else:
                error = validate_password(password)

            if error:
                return render(request, "users.html", {"error": error})

            # update_fields=['role']
            # Assign default role (User) during signup
            User.objects.create(username=username, email=email, password=make_password(password), role=role_to_assign)
            messages.success(request, "User created successfully!")


        elif action == "update_user" and user.role.name in ["Admin", "Manager"]:
            username = request.POST.get("username")
            new_email = request.POST.get("email")
            new_role_name = request.POST.get("role")

            user_to_update = get_object_or_404(User, username=username)

            # Managers can only update Users, not Managers or Admins
            if user.role.name == "Manager" and user_to_update.role.name != "User":
                messages.error(request, "Managers can only update Users.")
                return redirect("user")

            # Update Email
            if new_email and user_to_update.email != new_email:
                if User.objects.filter(email=new_email).exclude(username=username).exists():
                    messages.error(request, "Email already in use.")
                    return redirect("user")
                user_to_update.email = new_email

            # Update Role
            if new_role_name:
                if user.role.name == "Manager" and new_role_name != "User":
                    messages.error(request, "Managers can only assign the User role.")
                    return redirect("user")

                new_role = get_object_or_404(Role, name=new_role_name)
                user_to_update.role = new_role

            user_to_update.save()
            messages.success(request, "User details updated successfully.")


        elif action == "delete_user":

            user = get_object_or_404(User, id=request.POST["user_id"])

            if user.role.name == "Admin":
                messages.error(request, "Admins cannot delete other Admins.")
            else:
                user.delete()
                messages.success(request, "User deleted successfully.")

            return redirect("user")  # Ensure redirection after deletion

        return redirect("user")

    return render(request, "users.html", {"user": user,"users": users, "roles": roles})
