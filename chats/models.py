from django.contrib.postgres.fields import ArrayField
from django.db import models
from django_extensions.db.models import TimeStampedModel


# Create your models here.


class ChatHistory(TimeStampedModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    query = models.TextField(null=True, blank=True, default=None)
    response = models.TextField(null=True, blank=True, default=None)
    recommend_queries = ArrayField(models.CharField(max_length=300), blank=True, null=True)


class ChatHistoryReference(TimeStampedModel):
    chat_history = models.ForeignKey("chats.ChatHistory", on_delete=models.CASCADE)
    original_document = models.ForeignKey("sources.OriginalDocument", on_delete=models.CASCADE)
