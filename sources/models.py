from datetime import datetime

from django.db import models
from django_extensions.db.models import TimeStampedModel

from cores.models import SoftDeleteModel
from sources.enums import DataSourceEnum


# Create your models here.


class DataSource(TimeStampedModel):
    source = models.CharField(null=True, blank=True, choices=DataSourceEnum.choices())
    name = models.CharField(max_length=30, blank=True)
    description = models.CharField(max_length=200, blank=True)
    icon = models.CharField(max_length=200, blank=True)
    limit_count = models.IntegerField(null=True, blank=True, default=None)
    is_available = models.BooleanField(default=False)


class DataSyncStatus(TimeStampedModel, SoftDeleteModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    data_source = models.ForeignKey("sources.DataSource", null=True, blank=True, default=None, on_delete=models.CASCADE)
    account_name = models.CharField(max_length=100, null=True, blank=True, default=None)
    source = models.CharField(null=True, blank=True, choices=DataSourceEnum.choices())
    last_sync_datetime = models.DateTimeField(null=True, blank=True, default=None)
    cur_page_count = models.IntegerField(default=None, null=True, blank=True)
    total_page_count = models.IntegerField(default=None, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'source'], name='user source unique')
        ]

    @property
    def is_running(self):
        if self.source == DataSourceEnum.notion:
            return False if self.cur_page_count >= self.total_page_count else True


class OriginalDocument(TimeStampedModel, SoftDeleteModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    url = models.CharField(max_length=500, blank=True, null=True, default=None)
    title = models.TextField(blank=True, default="")
    text = models.TextField(blank=True, default="")
    text_hash = models.TextField(blank=True, default="")
    data_source = models.ForeignKey("sources.DataSource", null=True, blank=True, default=None, on_delete=models.CASCADE)
    source = models.CharField(null=True, blank=True, choices=DataSourceEnum.choices())

    class Meta:
        get_latest_by = 'created'


class NotionPage(TimeStampedModel, SoftDeleteModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    url = models.TextField(blank=True, null=True, default=None)
    page_id = models.CharField(max_length=300, null=True, default=None)
    title = models.TextField(blank=True, null=True, default=None)
    icon = models.CharField(max_length=250, null=True, default=None)
    is_workspace = models.BooleanField(default=False)


class DataSourceUpvote(TimeStampedModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    data_source = models.ForeignKey("sources.DataSource", on_delete=models.CASCADE)
