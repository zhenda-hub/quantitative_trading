from django.http import HttpResponse
from django.views import View
from django.shortcuts import render, redirect
from django.views.generic import CreateView, FormView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .forms import CreateUserForm, LoginForm
from django.contrib import messages
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.


class RegisterView(CreateView):
    form_class = CreateUserForm
    template_name = 'register.html'
    success_url = 'login'


class LoginView(FormView):
    form_class = LoginForm
    template_name = 'login.html'
    success_url = '/'

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)  # 验证
        login(self.request, user)
        return super(LoginView, self).form_valid(form)


def logout_user(request):
    logout(request)
    return redirect('login')


def index(request):
    return render(request, 'index.html')

# def register(request):
#     return render(request, 'login.html')