"""
URL configuration for CareerViceProject1 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from CareerViceApp1 import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Core Pages
    path('', views.home_view, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Forms
    path('load_form/', views.load_form, name='load_form'),
    path('submit_form/', views.submit_form, name='submit_form'),

    # Suggestions
    path('suggestions/', views.suggestions_view, name='suggestions'),

    # Result
    path('result/', views.result_view, name='result'),
    path('suggestion/<int:id>/', views.view_suggestion, name='view_suggestion'), 
]

