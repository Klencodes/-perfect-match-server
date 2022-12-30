
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate
from rest_framework import serializers
from django.contrib import auth
from .models import *

class CreateStaffSerializer(serializers.ModelSerializer):
    # password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    email = serializers.CharField(max_length=150)

    class Meta:
        model = User
        fields = ('email', 'last_name', 'first_name', 'user_type')
        # extra_kwargs = {'password': {'write_only': True}, }

    def create(self, validated_data):
        user = User.objects.create_staffuser(**validated_data)
        return user

'''
Phone Serializers
'''
class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)

    class Meta:
        model = User
        fields = ('email', 'phone_number', 'user_type', 'password')

    def create(self, validated_data):
        user = User.objects._create_user(**validated_data)
        return user

class BulkUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'phone_number', 'user_type', 'gender', 'is_verified' )

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password', 'groups', 'user_permissions' ] 

class SignInManagerSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            if User.objects.filter(email=email).exists():
                user = authenticate(request=self.context.get('request'), email=email, password=password)
            else:
                raise AuthenticationFailed({"response": "FAILED", "message": "Email is not registered"})
            if not user:
                raise AuthenticationFailed({"response": "FAILED", "message": "Invalid credentials, try again."})
        else:
            raise AuthenticationFailed({"response": "FAILED", "message": "Credential must include email and password"})

        attrs['user'] = user
        return attrs

class SignInUserSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

    def validate(self, attrs):
        phone = attrs.get('phone_number')
        password = attrs.get('password')

        if phone and password:
            if User.objects.filter(phone_number=phone).exists():
                user = authenticate(request=self.context.get('request'), phone_number=phone, password=password)
            else:
                raise AuthenticationFailed({"response": "FAILED", "message": "Phone number is not registered"})
            if not user:
                raise AuthenticationFailed({"response": "FAILED", "message": "Invalid credentials, try again."})
        else:
            raise AuthenticationFailed({"response": "FAILED", "message": "Credential must include phone number and password"})

        attrs['user'] = user
        return attrs


class ForgetPasswordSerializer(serializers.Serializer):
    """
    Used for resetting password who forget their password via otp varification
    """
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

'''
Email Phone seriliazers
'''
class ChangePasswordSerializer(serializers.Serializer):
    """
    password change (Login required)
    not using modelserializer as this serializer will be used for for two apis
    """
    current_password = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

'''
Email seriliazers
'''
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    confirm_password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    default_error_messages = {'detail': 'Name field should only contain alphanumeric characters'}

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone_number', 'password', 'confirm_password', 'user_type')

    def validate(self, attrs):
        first_name = attrs.get('first_name', '')
        if not first_name.isalnum():
            raise serializers.ValidationError(self.default_error_messages)
        return attrs

    def create(self, validated_data):
        return User.objects._create_user(**validated_data)

class EmailVerificationSerializer(serializers.ModelSerializer):
    token = serializers.CharField(max_length=555)

    class Meta:
        model = User
        fields = ['token']
     
class LoginSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'tokens']

    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')
        filtered_user_by_email = User.objects.filter(email=email)
        user = auth.authenticate(email=email, password=password)

        if filtered_user_by_email.exists() and filtered_user_by_email[0].auth_provider != 'EMAIL':
            raise AuthenticationFailed(
                detail='Please continue your login using ' + filtered_user_by_email[0].auth_provider)

        if not user:
            raise AuthenticationFailed('Invalid credentials, try again')
        if not user.is_active:
            raise AuthenticationFailed('Account disabled, contact admin')
        if not user.is_verified:
            raise AuthenticationFailed('Email is not verified')

        return {
            'email': user.email,
            'username': user.username,
            'tokens': user.tokens
        }

        return super().validate(attrs)

class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=3)
    redirect_url = serializers.CharField(max_length=500, required=False)

    class Meta:
        fields = ['email']

class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6, max_length=68, write_only=True)
    confirm_password = serializers.CharField(min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(min_length=1, write_only=True)
    uidb64 = serializers.CharField(min_length=1, write_only=True)

    class Meta:
        fields = ['password', 'confirm_password', 'token', 'uidb64']

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            confirm_password = attrs.get('confirm_password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')

            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('The reset link is invalid',)
            if password != confirm_password:
                return Response({'status_code': 101, 'detail': 'Passwords do not match'})
            user.set_password(password)
            user.save()

            return (user)
        except Exception as e:
            raise AuthenticationFailed('The reset link is invalid', 401)
        return super().validate(attrs)

'''
Users data 

'''
class AddressPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        exclude = ['user']
        
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        exclude = []

class AddressDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        exclude = ['user']
    def to_representation(self, instance):
        response=super().to_representation(instance)
        response['user']=UserSerializer(instance.user).data['full_name']
        return response
        