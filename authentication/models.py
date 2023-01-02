from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager, PermissionsMixin, Group)
from rest_framework.authtoken.models import Token
from django.core.validators import RegexValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
# from django.utils import timezone
from django.db import models
from .utils import *
class Group(models.Model):
    group_id=models.OneToOneField(Group, on_delete=models.CASCADE, blank=True, null=True)
    title=models.CharField(max_length=50, blank=True, null=True, unique=True)
    description=models.CharField(max_length=255, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    def __str__(self):
        return str(self.title)

class UserManager(BaseUserManager):
    def create_user(self, first_name, last_name, email, user_type, password=None, password_confirm=None):
        if password is None:
            raise TypeError('User should have a password')
        if email is None:
            raise TypeError('User should have a Email')
        user = self.model(first_name=first_name, last_name=last_name, user_type=user_type, email=self.normalize_email(email))
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, first_name, last_name, user_type, password=None ):
        if email is None:
            raise TypeError('User must have email')
        if password is None:
            raise TypeError('User must have password')

        user = self.model(first_name=first_name, last_name=last_name, user_type=user_type, email=self.normalize_email(email))
        user.set_password(password)
        user.is_superuser = True
        user.verified_phone = True
        user.verified_email = True
        user.is_staff = True
        user.user_type = "ADMIN"
        user.save()
        return user

    def _create_user(self, email, phone_number, user_type, password=None, ):
        if phone_number is None:
            raise TypeError('User must have phone number')
        if password is None:
            raise TypeError('User must have password')
        
        user = self.model(user_type=user_type, phone_number=phone_number, email=self.normalize_email(email))
        user.set_password(password)
        user.save()
        return user

AUTH_PROVIDERS = { 'EMAIL': 'EMAIL', 'PHONE':'PHONE', 'FACEBOOK': 'FACEBOOK', 'GOOGLE': 'GOOGLE', 'TWITTER': 'TWITTER',}

USERTYPE_CHOICES=(('ADMIN', 'ADMIN'), ('STAFF', 'STAFF'), ('DRIVER', 'DRIVER'), ('CUSTOMER', 'CUSTOMER'))
phone_regex = RegexValidator( regex=r'^\+?1?\d{9,14}$', message ="Phone number must be entered in the format: '+999999999'. Up to 14 digits allowed.")

class User(AbstractBaseUser, PermissionsMixin):
    # group_id = models.ManyToManyField(Group, related_name="group_id", default=1)
    user_type = models.CharField(max_length=20, choices=USERTYPE_CHOICES, default='CUSTOMER')
    first_name = models.CharField(max_length=150, )
    last_name = models.CharField(max_length=150,)
    gender = models.CharField(max_length=10)
    prefered_gender = models.CharField(max_length=10)
    username = models.CharField(max_length=255, unique=True, db_index=True, null=True,)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField( max_length=255, unique=True, null=True, blank=True)
    birth_date = models.DateTimeField(null=True)
    verified_phone = models.BooleanField(default=False)
    verified_email = models.BooleanField(default=False)
    deactivated = models.BooleanField(default=False)
    onboarding_completed = models.BooleanField(default=False)
    onboarding_percentage = models.CharField(max_length=5, default="0")
    is_staff = models.BooleanField(default=False)
    is_loggedin = models.BooleanField(default=False)
    first_login = models.BooleanField(default=False)
    allow_push_notification = models.BooleanField(default=False)
    profile_picture = models.TextField(null=True, blank=True, default="")
    auth_provider = models.CharField(max_length=15, blank=False, null=False, default=AUTH_PROVIDERS.get('PHONE'))
    phone_number = models.CharField(validators=[phone_regex], max_length=17, null=True, unique=True)
    signup_date = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'user_type']
    objects = UserManager()

    def save(self, *args, **kwargs):
        self.full_name = '{0} {1}'.format(self.first_name, self.last_name)
        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.full_name)

@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

class PhoneOTP(models.Model):
    phone_regex = RegexValidator( regex   =r'^\+?1?\d{9,14}$', message ="Phone number must be entered in the format: '+999999999'. Up to 14 digits allowed.")
    phone_number= models.CharField(validators=[phone_regex], max_length=17, unique=True)
    otp         = models.CharField(max_length = 9, blank = True, null= True)
    count       = models.IntegerField(default = 0, help_text = 'Number of otp sent')
    logged      = models.BooleanField(default = False, help_text = 'If otp verification got successful')
    forgot      = models.BooleanField(default = False, help_text = 'only true for forgot password')
    forgot_logged = models.BooleanField(default = False, help_text = 'Only true if validdate otp forgot get successful')

    def __str__(self):
        return str(self.phone_number) + ' is sent ' + str(self.otp)

class Address(models.Model):
    user = models.ForeignKey(User, related_name="user_address", on_delete=models.CASCADE)
    country = models.CharField(max_length=100, blank=False, null=False)
    city = models.CharField(max_length=100, blank=False, null=False)
    street_address = models.CharField(max_length=255, blank=False, null=False)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    is_home_address = models.BooleanField(default=False)
    is_billing_address = models.BooleanField(default=False)
    state = models.CharField(max_length=255, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    objects = UserManager()

    def __str__(self):
        return str(self.user.full_name) + ' Lives in ' + str(self.city)

class File(models.Model):
    image = models.FileField(upload_to=upload_image_path_profile, blank=False, null=False)
    objects=models.Manager()
    def __str__(self):
        return self.image.name