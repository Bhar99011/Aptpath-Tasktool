from django.urls import path

from user import views

urlpatterns = [
    path('', views.signup_fun, name='signup'),
    path('login', views.login_fun, name='login'),
    path('logout', views.logout, name='logout'),
    path('profile', views.profile, name='profile'),
    path('tasks', views.tasks_view, name='task'),
    path('users', views.users_view, name='user'),
]