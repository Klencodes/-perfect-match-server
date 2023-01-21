from django.contrib import admin
from .models import *

# Register your models here.

class LikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'liked_user', 'created_at', ]


class MatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_liking', 'liked_user', 'created_at',]

class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat_room', 'user', 'message', 'read', 'created_at',]

admin.site.register(Like, LikeAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)
admin.site.register(ChatRoom)