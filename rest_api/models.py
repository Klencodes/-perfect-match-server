from django.db import models
from authentication.models import *
class Like(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    liked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'liked_user')

    
class Match(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_liking = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_1')
    liked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_2')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user_liking', 'liked_user')

class ChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    image = models.TextField()
    participants = models.ManyToManyField(to=User, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_online_count(self):
        return self.participants.count()

    def join(self, user):
        self.participants.add(user)
        self.save()

    def leave(self, user):
        self.participants.remove(user)
        self.save()

    def __str__(self):
        return f'{self.name} ({self.get_online_count()})'

class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE) 
    sender = models.ForeignKey(User, on_delete=models.CASCADE, )
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.first_name}: {self.message} [{self.created_at}]'
class PaymentCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    authorize_payment = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    card_number = models.CharField(max_length=16)
    type = models.CharField(max_length=16)
    cvc = models.CharField(max_length=4)
    expiry_date = models.CharField(max_length=5)
    card_holder = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.first_name}: {self.is_primary} [{self.created_at}]'