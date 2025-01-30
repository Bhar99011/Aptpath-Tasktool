from django.urls import path

from user import views

urlpatterns = [
    path('', views.signup_fun, name='signup'),
    path('login', views.login_fun, name='login'),
    path('logout', views.logout, name='logout'),
    path('admin_dash', views.admin_dash_func, name='admin_dash'),
    path('manager_dash', views.manager_dash_func, name='manager_dash'),
    path('user_dash', views.user_dash_func, name='user_dash')
]