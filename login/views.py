from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import View


# Create your views here.
# def login(request):
#     return render(request, 'login.html')
class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        pass


class RegisterView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        pass


# def register(request):
#     return render(request, 'login.html')