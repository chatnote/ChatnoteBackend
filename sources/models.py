from datetime import datetime

from django.db import models
from django_extensions.db.models import TimeStampedModel

from cores.models import SoftDeleteModel
from sources.enums import DataSourceEnum, SyncStatusEnum


# Create your models here.


class DataSyncStatus(TimeStampedModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    source = models.CharField(null=True, blank=True, choices=DataSourceEnum.choices())
    is_running = models.BooleanField(default=False)
    last_sync_datetime = models.DateTimeField(null=True, blank=True, default=None)
    cur_page_count = models.IntegerField(default=None, null=True, blank=True)
    total_page_count = models.IntegerField(default=None, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'source'], name='user source unique')
        ]

    @property
    def status(self):
        current_datetime = datetime.now()

        if self.is_running:
            return SyncStatusEnum.running
        else:
            if current_datetime is None:
                return SyncStatusEnum.allow
            elif current_datetime.timestamp() - self.last_sync_datetime.timestamp() < 3600 * 24:
                return SyncStatusEnum.disallow
            else:
                return SyncStatusEnum.allow


class OriginalDocument(TimeStampedModel, SoftDeleteModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    url = models.CharField(max_length=500, blank=True, null=True, default=None)
    title = models.TextField(blank=True, default="")
    text = models.TextField(blank=True, default="")
    text_hash = models.TextField(blank=True, default="")
    source = models.CharField(null=True, blank=True, choices=DataSourceEnum.choices())

    class Meta:
        get_latest_by = 'created'


class NotionPage(TimeStampedModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    url = models.TextField(blank=True, null=True, default=None)
    page_id = models.CharField(max_length=300, null=True, default=None)
    title = models.TextField(blank=True, null=True, default=None)
    icon = models.CharField(max_length=250, null=True, default=None)
    is_workspace = models.BooleanField(default=False)
