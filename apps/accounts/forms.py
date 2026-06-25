from django import forms
from .models import CustomUser
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate

class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        label="Password"
    )

    class Meta:
        model = CustomUser
        fields = [
            'email',
            'password',
            'date_of_birth', 
            'full_name',
            'username', 
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'full_name': forms.TextInput(attrs={'placeholder': 'Full Name'}),
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        if email=="": 
            raise forms.ValidationError("Please enter a valid email address. ")   
        return email 

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth','')
        if dob is None:
            raise ValidationError("Select your birthday.")
        return dob

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name','')
        if name == "":
            raise ValidationError("Enter your name.")
        return name

class UniversalLoginForm(forms.Form):
    username = forms.CharField(
        label="",
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Mobile number, Email, or Username',
            'class': 'form-control'
        })
    )

    password = forms.CharField(
        label="",
        required=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'class': 'form-control'
        })
    )
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username', '').strip()
        password = self.cleaned_data.get('password', '')

        if password == "" and username == "":
            raise ValidationError({"username": "Please enter a valid username.",
                "password": "Please enter a valid password."})
        if username == "" or password=="":
            if username == "":
                raise ValidationError({"username": "Please enter a valid username."})   
            elif password=="":
                raise ValidationError({"password": "Please enter a valid password."})

        if username and password:
            self.user_cache = authenticate(
                self.request, 
                username=username, 
                password=password
            )
            
            if self.user_cache is None:
                raise ValidationError(
                    "Invalid login credentials. Please try again."
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

