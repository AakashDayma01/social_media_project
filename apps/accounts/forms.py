from django import forms
from .models import CustomUser
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate

class CustomUserCreationForm(forms.ModelForm):
    """
    Form for handling new user registration.
    Enforces field requirement rules and securely hashes the user's
    chosen password before saving it to the database.
    """
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
        """
        Hashes the plain-text password and saves the user instance.
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

    def clean_email(self):
        """
        Validates that the email field is not empty.
        """
        email = self.cleaned_data.get('email', '')
        if email=="": 
            raise forms.ValidationError("Please enter a valid email address. ")   
        return email 

    def clean_date_of_birth(self):
        """
        Validates that a birthday has been chosen.
        """
        dob = self.cleaned_data.get('date_of_birth','')
        if dob is None:
            raise ValidationError("Select your birthday.")
        return dob

    def clean_full_name(self):
        """
        Validates that the full name field is not empty.
        """
        name = self.cleaned_data.get('full_name','')
        if name == "":
            raise ValidationError("Enter your name.")
        return name

class UniversalLoginForm(forms.Form):
    """
    Multi-identifier login form with authentication caching.

    Accepts an email, phone number, or username alongside a password,
    then queries the authentication backend.
    """
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
        """
        Stores the current HTTP request to forward context to auth backends.
        """
        self.request = request
        super().__init__(*args, **kwargs)

    def clean(self):
        """
        Verifies credentials, checks account status, and populates the user cache.
        """
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
                if not self.user_cache.is_active:
                    raise ValidationError("This account is currently inactive.")

        return self.cleaned_data


class OTPRequestForm(forms.Form):
    """
    Form to request a One-Time Password reset token.
    """
    email = forms.EmailField(
        label="Enter Email",
        error_messages={
            'required': 'Please enter an email address.',
            'invalid': 'Please enter a valid email address.'
        },
         widget=forms.TextInput(attrs={
            'placeholder': 'Enter your registered email',
            'class': 'form-control'
        })
    )
    
