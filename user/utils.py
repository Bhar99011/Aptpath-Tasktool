from django.shortcuts import redirect

def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            user = User.objects.get(id=request.session.get('user_id'))
            if user.role.name in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                return redirect('login')  # Redirect to login or a forbidden page
        return wrapper_func
    return decorator
