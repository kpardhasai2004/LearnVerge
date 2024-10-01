from django.db import models

class ChatCollection(models.Model):
    name = models.CharField(unique=True, max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Chat(models.Model):
    collection = models.ForeignKey(ChatCollection, on_delete=models.CASCADE, related_name='chats')
    user_input = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user_input[:50]
