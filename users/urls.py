# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('main/', views.main_page, name='main'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('update_role/<int:user_id>/', views.update_role, name='update_role'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/manager/', views.manager_dashboard, name='manager_dashboard'),
    path('dashboard/executive/', views.executive_dashboard, name='executive_dashboard'),
    path('assign-task/', views.assign_task, name='assign_task'),
    path('task-list/', views.task_list, name='task_list'),
    path('assign-task/<int:user_id>/', views.assign_task, name='assign_task'),
    path('assign-task/', views.assign_task, name='assign_task'),
    path('logout/', views.logout_view, name='logout'),
    path('submit-task/<int:task_id>/', views.submit_task, name='submit_task'),
]

