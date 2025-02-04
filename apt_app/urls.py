from django.urls import path
from apt_app import views

urlpatterns = [
    path("", views.login,name="login"),
    path("signup/", views.signup,name="signup1"),
    path("logout/", views.logout,name="logout"),
    path('dashboard/<int:user_id>/', views.dashboard, name='dashboard'),
    path('manager_dashboard/<int:user_id>/', views.manager_dashboard, name='manager_dashboard'),
    path('admin_dashboard/<int:user_id>/', views.admin_dashboard, name='admin_dashboard'),
    path('user_delete/<int:user_id>/', views.user_delete, name='user_delete'),
    path("create_user/", views.create_user,name="create_user"),
    path("update_role/<int:user_id>", views.update_role, name="update_role"),
    path("tasks/<int:user_id>",views.tasks, name="tasks"),
    path("task_action/<int:task_id>", views.task_action , name="task_action"),
    path("user_edit<int:user_id>",views.user_edit, name="user_edit"),
]
