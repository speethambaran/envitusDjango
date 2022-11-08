from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('users/', views.users, name='users'),
    path('users/roles/', views.roles, name='roles'),
    path('getusers/', views.getusers, name='getusers'),
    path('enableusers/', views.enableusers, name='enableusers'),
    path('disableusers/', views.disableusers, name='disableusers'),
    path('deleteuser/', views.deleteuser, name='deleteuser'),
]
