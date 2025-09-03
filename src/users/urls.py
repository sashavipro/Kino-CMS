from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # ---USER---
    path('login/', views.login_view, name='login'),
    path('registrarion/', views.registrarion_view, name='registration'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
]