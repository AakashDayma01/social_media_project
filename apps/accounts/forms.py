from django import forms
from .models import CustomUser
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm

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

class UniversalLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username, Email, or Mobile Number",
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your Username, Email, or Mobile',
            'class': 'form-control'
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username', '')
        if username=="": 
            raise forms.ValidationError("Please enter a valid username. ")   
        return username 

    def clean_password(self):
        password = self.cleaned_data.get('password','')
        if password == "":
            raise ValidationError("Please enter a valid password. ")
        return password


