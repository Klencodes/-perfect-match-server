from django.contrib import admin

# Register your models here.
from .models import *


class UserAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'auth_provider', 'phone_number', 'user_type', 'signup_date', 'date_updated']


class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = [ 'id', 'otp', 'phone_number', 'count', 'logged', 'forgot', 'forgot_logged']

admin.site.register(PhoneOTP, PhoneOTPAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Group)
admin.site.register(Address)
