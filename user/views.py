from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

from user.forms import CreateUserForm

# Create your views here.


class RegisterView(CreateView):
    form_class = CreateUserForm
    template_name = 'register.html'
    # template_name = 'login.html'
    success_url = 'login'


class MyLoginView(CreateView):
    form_class = CreateUserForm
    template_name = 'login.html'
    success_url = 'login'

# def user_login(request):




def logout_user(request):
    logout(request)
    return redirect('login')

