from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from . import forms
from .forms import RegisterUserForm

def register(request):
    if request.method == 'POST':
        form_user_register = RegisterUserForm(request.POST)
        if form_user_register.is_valid():
            form_user_register.save()
            return redirect('login')
    else:
        form_user_register = RegisterUserForm()

    context = {'form_user_register': form_user_register}
    return render(request, 'users/register.html.jinja', context)

def user_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Nieprawidłowa nazwa użytkownika lub hasło.")
    
    return render(request, "users/login.html.jinja")



def user_logout(request):
    logout(request)
    return redirect("login")



@login_required(login_url='login')
def dashboard(request):
    return render(request, "users/dashboard.html.jinja", {"user": request.user})