from django.contrib import admin
from .models import *

# Register your models here.

class LikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'liked_user', 'created_at', ]


class MatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_liking', 'liked_user', 'created_at',]

admin.site.register(Like)
admin.site.register(ChatMessage)
admin.site.register(ChatHistory)
admin.site.register(Match)