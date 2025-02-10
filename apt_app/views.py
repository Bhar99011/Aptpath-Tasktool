from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.hashers import check_password, make_password
from django.contrib import messages
from apt_app.models import users_details,Tasks
from apt_app import validations
from django.core.paginator import Paginator,EmptyPage
from django.db.models import Q



def login(request):
   
    if request.method == "POST":
        user_name = request.POST.get("user_name")
        password = request.POST.get("password")
        user = users_details.objects.filter(user_name=user_name).first()

        if user and check_password(password, user.password):
            request.session['user_id'] = user.id  # Store user ID in session
            messages.success(request, "Login Successful!")
            
            if user.role == "admin":
                return redirect(admin_dashboard, user_id=user.id)
            elif user.role == "manager":
                return redirect("manager_dashboard", user_id=user.id)
            else:
                return redirect(dashboard, user_id=user.id)
        elif user:
            messages.error(request, "Invalid password.")
        else:
            messages.error(request, "User not found.")

    return render(request, "login.html")


def signup(request):
    if request.method == "POST":
        user_name = request.POST.get("user_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("conform_password")
        hashed_password = make_password(password)

        is_valid_username = validations.username_validation(request, user_name)
        is_valid_email = validations.email_validation(request, email)
        is_valid_password = validations.password_validation(request, password, confirm_password)

        if is_valid_email and is_valid_password and is_valid_username:
            users_details.objects.create(
                user_name=user_name,
                email=email,
                password=hashed_password
            )
            messages.success(request, "Sign-up successful! Please log in.")
            return redirect("login")

    return render(request, "signup.html")


def dashboard(request, user_id):
    
    session_user_id = request.session.get('user_id')

    if session_user_id != user_id:
        messages.error(request, "Unauthorized access.")
        return redirect("login")

    user = users_details.objects.filter(id=user_id).first()
    search=request.GET.get("search","").strip()
    if search:
        tasks=Tasks.objects.filter(title__icontains=search,assigned_to=user).order_by("-created_at") 
    else: 
        tasks = Tasks.objects.filter(assigned_to=user).order_by("-created_at")
    p=Paginator(tasks,2)
    page=request.GET.get("page")
    tasks=p.get_page(page)
    
    users=users_details.objects.all()
    
    
    context = {
        'user_id':user_id,
        'user_name': user.user_name,
        'role': user.role,
        "tasks":tasks,
        "users":users,
        "search_query":search,
    }

    if request.method == "POST":   

        select=request.POST.get("select")
        
        if select == "create_task":
            # Retrieve form data
            title = request.POST.get("title")
            description = request.POST.get("description")
            assigned_to_user = request.POST.get("assigned_to")

            try:
                # Fetch assigned_to user object by username
                assigned_to = users_details.objects.get(user_name=assigned_to_user)
                # Fetch the assigned_by user object
                assigned_user = users_details.objects.get(id=user_id)
                
            except users_details.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect("dashboard", user_id=user_id)

            assigned_by = assigned_user  # Pass the entire object here, not just the user_name

            # Create the task
            Tasks.objects.create(
                title=title,
                description=description,
                assigned_to=assigned_to,
                assigned_by=assigned_by  # Pass the instance of users_details
            )

            # Success message
            messages.success(request, "Task Created Successfully!")              
    
    
    return render(request, "dashboard.html", context)


def logout(request):
    request.session.flush()  # Clears the session
    messages.info(request, "You have been logged out.")
    return redirect("login")


def admin_dashboard(request, user_id):
    # Logic for admin dashboard
    session_user_id = request.session.get('user_id')
    session_user = users_details.objects.filter(id=user_id).first()

    if session_user_id != user_id or session_user.role !="admin":
        messages.error(request, "Unauthorized access.")
        return redirect("login")

    user = users_details.objects.filter(id=user_id).first()
    
    if not user:
        messages.error(request, "User not found.")
        return redirect("login")
    
    search=request.GET.get("search","").strip()
    print(search)
    if search:
        user_info=users_details.objects.filter(user_name__icontains=search)
    else:
        user_info=users_details.objects.all()
    p = Paginator(user_info, 2)  # Show 10 objects per page
    page_number = request.GET.get("page")    
    user_info =p.get_page(page_number) 

    user_count = users_details.objects.count()
    manager_count=users_details.objects.filter(role="manager").count()
    task_count = Tasks.objects.count()
    

    context = {
        "user_name":user,
        'user_info': user_info,
        'role': user.role,
        "user_id":user_id,
        "user_count":user_count,
        "task_count":task_count,
        "manager_count":manager_count,
        "search_query":search,
    }
    return render(request, "admin_dashboard.html", context)
    


def manager_dashboard(request, user_id):
   
    # Logic for manager dashboard
    session_user_id = request.session.get('user_id')  

    if session_user_id != user_id:
        messages.error(request, "Unauthorized access.")
        return redirect("login")

    user = users_details.objects.filter(id=user_id).first()
    if not user:
        messages.error(request, "User not found.")
        return redirect("login")
    
    search=request.GET.get("search","").strip()
    if search:
        user_list=users_details.objects.filter(user_name__icontains=search,role="user")
    else:
        user_list = users_details.objects.filter(role="user")
    p=Paginator(user_list,2)
    page=request.GET.get("page")
    user_list=p.get_page(page)

    user_count=users_details.objects.filter(role="user").count()
    tasks_count=Tasks.objects.all().count()

    context = {
        'user_name': user.user_name,
        'role': user.role,
        "user_info":user_list,
        "user_id":user_id,
        "user_count":user_count,
        "task_count":tasks_count,
        "search_query":search,
    }

    return render(request, "manager_dashboard.html", context)

def user_delete(request, user_id):
    session_user_id=request.session.get('user_id')
    session_user = get_object_or_404(users_details, id=session_user_id)
    allowed_admins=[]
    user=users_details.objects.get(id=user_id)

    if user.role != "admin":
        if request.method=="POST":
            user=users_details.objects.get(id=user_id)
            user.delete()
            messages.success(request,"User deleted Sucessfully")
            if session_user.role == "manager":
                return redirect("manager_dashboard",session_user_id )

            else:
                return redirect("admin_dashboard",session_user_id )
    elif user.role == "admin" and session_user.role=="admin":
        if session_user in allowed_admins :
            user.delete()
            messages.success(request,"User deleted Sucessfully")
            return redirect("admin_dashboard",session_user_id )
        else:
            messages.error(request,"You are not autherize to Delete this admin")
       
        
    return redirect(f"{session_user.role}_dashboard",user_id=session_user_id)

def user_edit (request,user_id):
    session_user_id=request.session.get("user_id")
    if not session_user_id:
        messages.error(request, "Unauthorized access.")
        return redirect("login")  # Redirect to login if not logged in

    session_user = get_object_or_404(users_details, id=session_user_id)
    if request.method=="POST":
        email=request.POST.get("email")
        user=users_details.objects.get(id=user_id)
        user.email=email
        user.save()
        print(user.id,user_id)
        messages.success(request,f"{user.user_name}'s Detais changed sucessfully .. ")
    return redirect(f"{session_user.role}_dashboard",user_id=session_user_id)



def create_user(request):
    session_user_id=request.session.get("user_id")
    session_user=get_object_or_404(users_details,id=session_user_id)
    if request.method=="POST":
        user_name=request.POST.get("user_name")
        email=request.POST.get("email")
        password=request.POST.get("password")
        confirm_password=request.POST.get("confirm_password")
        hashed_password = make_password(password)

        is_valid_username = validations.username_validation(request, user_name)
        is_valid_email = validations.email_validation(request, email)
        is_valid_password = validations.password_validation(request, password, confirm_password)

        if is_valid_email and is_valid_password and is_valid_username:
            users_details.objects.create(
                user_name=user_name,
                email=email,
                password=hashed_password
            )
            messages.success(request, " User Added successful!")
            return redirect(f"{session_user.role}_dashboard",user_id=session_user_id)

        
    return redirect(f"{session_user.role}_dashboard",user_id=session_user_id)
def update_role(request,user_id):
    if request.method == "POST":
        user=users_details.objects.get(id=user_id)
        session_user_id = request.session.get("user_id")
        session_user = users_details.objects.filter(id=session_user_id).first()
        print(session_user,session_user.user_name)
        update_user_role=request.POST.get("role")

        allowed_admins=["admin"]

        if update_user_role !="admin":
            user.role=update_user_role
            user.save()
            messages.success(request,"User Role Updated Sucessfull !")
            #redirect("admin_dashboard",user_id=request.session.get("user_id"))
        
        elif update_user_role == "admin" and session_user.user_name in allowed_admins:
            user.role=update_user_role
            user.save()
            messages.success(request,"User Role Updated Sucessfull !")     
        else:
            messages.error(request,"You Not Autherised to Change Role ")
            
        


    return redirect("admin_dashboard",user_id=request.session.get("user_id"))


def tasks(request,user_id):
    # Retrieve the session user
    session_user_id = request.session.get("user_id")

    # Get the user or return a 404 error if not found
    session_user = get_object_or_404(users_details, id=session_user_id)
    

    # If user is not authenticated (session_user is None), redirect to login
    if not session_user:
        messages.error(request, "Unauthorized access.")
        return redirect("login")
    if session_user.role == "admin":
        dashboard_url = "admin_dashboard"
    elif session_user.role == "manager":
        dashboard_url = "manager_dashboard"
    else:
        dashboard_url = "/"


    users=users_details.objects.all()

    search=request.GET.get("search","").strip()
    if search:
        tasks=Tasks.objects.filter(title__icontains=search).order_by("-created_at")
    else:
        tasks=Tasks.objects.all().order_by("-created_at")
    p=Paginator(tasks,2)
    page=request.GET.get("page")
    tasks=p.get_page(page)

    context={
            "users":users,
            "user_id":user_id,
            "tasks":tasks,
            'user_name': session_user.user_name,
            'role': session_user.role,
            "dashboard_url": dashboard_url,  # Pass the dashboard URL to the template
            "search_query":search,
        }

    if request.method == "POST":   

        select=request.POST.get("select")
        
        if select == "create_task":
            # Retrieve form data
            title = request.POST.get("title")
            description = request.POST.get("description")
            assigned_to_user = request.POST.get("assigned_to")

            try:
                # Fetch assigned_to user object by username
                assigned_to = users_details.objects.get(user_name=assigned_to_user)
                # Fetch the assigned_by user object (current session user)
                assigned_by = session_user  # Assigned by the logged-in user
                
            except users_details.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect("tasks", user_id=user_id)

            #assigned_by = assigned_user  # Pass the entire object here, not just the user_name
            print(assigned_by)

            # Create the task
            Tasks.objects.create(
                title=title,
                description=description,
                assigned_to=assigned_to,
                assigned_by=assigned_by  # Pass the instance of users_details
            )

            # Success message
            messages.success(request, "Task Created Successfully!")
                   
    
    return render(request,"new_task.html",context)   

def task_action(request, task_id):
    l=Tasks.objects.get(id=task_id)
    print(l)
    session_user_id = request.session.get("user_id")
    
    if request.method == 'POST':
        select = request.POST.get("select")
        print(select)
        
        if select == "edit_task":
            title = request.POST.get("title")
            description = request.POST.get("description")
            assigned_to_user = request.POST.get("assigned_to")

            # Handle missing user gracefully
            try:
                assigned_to = users_details.objects.get(user_name=assigned_to_user)
                
            except users_details.DoesNotExist:
                messages.error(request, "Assigned user not found.")
                return redirect("tasks", session_user_id)

            task = get_object_or_404(Tasks, id=task_id)
            task.title = title
            task.description = description
            print("before assigned to ",task.assigned_to)
            task.assigned_to = assigned_to
            print('after',task.assigned_to)
            task.save()
            messages.success(request, "Task updated successfully!")

        elif select == "delete_task":
            task_delete = get_object_or_404(Tasks, id=task_id)
            task_title = task_delete.title  # Store before deleting
            task_delete.delete()
            messages.success(request, f"Task '{task_title}' has been deleted successfully.")
    
    return redirect("tasks", session_user_id)
       
def submit_answer(request,task_id):
    session_user_id=request.session.get("user_id")
    session_user=get_object_or_404(users_details,id=session_user_id)
    session_user_role=session_user.role
    if request.method=="POST":
        answer=request.POST.get("answer")
        task=Tasks.objects.get(id=task_id)
        task.answer=answer
        task.save()
        messages.success(request, "Your answer has been submitted successfully!")
    if session_user_role=="user":
        return redirect("dashboard",session_user_id)
    else:
        return redirect(f"tasks", session_user_id)
    



       