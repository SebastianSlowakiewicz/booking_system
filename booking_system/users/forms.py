from dataclasses import fields
from pyexpat import model
from django import forms
from django.contrib.auth.models import User

from django.contrib.auth.forms import UserCreationForm

from . import models

class RegisterUserForm(UserCreationForm):
    class Meta:
        model = models.Users
        # exclude = ['id']
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'birth_date', 'phone', 'identity_document_type', 'identity_document_no']
        birth_date = forms.DateField(
            widget=forms.DateInput(attrs={'type': 'date'}),
            input_formats=['%d.%m.%Y']
        )

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)