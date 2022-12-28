from django.contrib.auth.backends import ModelBackend
from .models import User

class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        if email is None:
            phone_number = kwargs.get('phone_number')
            if phone_number is None:
                return None
            else:
                try:
                    user = User.objects.get(phone_number=phone_number)
                except User.DoesNotExist:
                    return None
        else:
            try:
                user = User.objects.get(email=email)
            except user.Doesnotexist: 
                return None

        if user.check_password(password):
            return user
            
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None