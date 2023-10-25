from django.contrib.postgres.fields import ArrayField
from django.db import models
from django_extensions.db.models import TimeStampedModel

from chats.enums import ChatMessageEnum


# Create your models here.


class ChatSession(TimeStampedModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)


class ChatHistory(TimeStampedModel):
    session = models.ForeignKey("chats.ChatSession", null=True, blank=True, default=None, on_delete=models.CASCADE)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    message_type = models.CharField(max_length=20, null=True, blank=True, default=None, choices=ChatMessageEnum.choices())
    content = models.TextField(null=True, blank=True, default=None)
    recommend_queries = ArrayField(models.CharField(max_length=300), blank=True, null=True)
    original_document_ids = ArrayField(models.CharField(max_length=300), blank=True, null=True)
    eval_choice = models.IntegerField(null=True, blank=True, default=None)
    eval_message = models.TextField(null=True, blank=True, default=None)
