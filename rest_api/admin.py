from django.contrib import admin
from .models import *

# Register your models here.

class LikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'liked_user', 'created_at', ]


class MatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_liking', 'liked_user', 'created_at',]

class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'group', 'sender', 'message', 'read', 'created_at',]

class PaymentCardAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'authorize_payment', 'is_primary', 'card_number', 'type', 'cvc', 'expiry_date', 'card_holder']

admin.site.register(Like, LikeAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(PaymentCard, PaymentCardAdmin)
admin.site.register(Group)