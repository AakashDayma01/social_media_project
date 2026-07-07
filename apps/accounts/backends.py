from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class UniversalAuthBackend(ModelBackend):
    def authenticate(self, request, **kwargs):
        User = get_user_model()
        username = kwargs.get('username')
        password = kwargs.get('password')
        identifier = kwargs.get('username')
        if not identifier:
            return None
        try:    
            user = UserModel.objects.get(
                Q(username__iexact=identifier) | 
                Q(email__iexact=identifier) | 
                Q(phone_number=identifier)
            )
        except UserModel.DoesNotExist:
            return None
        
        if user.check_password(password):
            return user
        return None
