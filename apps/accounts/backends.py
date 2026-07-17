from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class UniversalAuthBackend(ModelBackend):
    """
    Custom authentication backend allowing login via multiple identifiers.

    Permits users to authenticate using their username, email address,
    or phone number interchangeably.
    """

    def authenticate(self, request, **kwargs):
        """
        Authenticate a user based on a unique identifier and password.
        """
        User = get_user_model()
        username = kwargs.get('username')
        password = kwargs.get('password')
        identifier = kwargs.get('username')
        
        if not identifier:
            return None
            
        try:    
            user = User.objects.get(
                Q(username__iexact=identifier) | 
                Q(email__iexact=identifier) | 
                Q(phone_number=identifier)
            )
        except User.DoesNotExist:
            return None
        
        if user.check_password(password):
            return user
        return None
