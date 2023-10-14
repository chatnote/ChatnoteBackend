from datetime import timedelta
from typing import List

from ninja import Schema
from pydantic.datetime_parse import datetime

from sources.enums import DataSourceEnum


class NotionCallbackParams(Schema):
    access_token: str


class SyncStatusSchema(Schema):
    source: DataSourceEnum
    total_page_count: int | None
    current_page_count: int | None
    is_running: bool

    @classmethod
    def from_instance(cls, data_sync_status):
        return cls(
            source=data_sync_status.source,
            total_page_count=data_sync_status.total_page_count,
            current_page_count=data_sync_status.cur_page_count,
            is_running=data_sync_status.is_running
        )

    @classmethod
    def from_instances(cls, data_sync_status_qs):
        return [cls.from_instance(data_sync_status) for data_sync_status in data_sync_status_qs]


class OriginalDocumentSchema(Schema):
    user_id: int
    data_source_type: DataSourceEnum
    url: str
    title: str
    text: str
    text_hash: str  # original text parsing 로직을 바꾸면 hash 값 업데이트

    @classmethod
    def from_dict(cls, item: dict):
        return cls(
            user_id=item['user_id'],
            data_source_type=item['data_source_type'],
            url=item['url'],
            title=item['title'],
            text=item['text'],
            text_hash=item['text_hash'],
        )


class NotionPageSchema(Schema):
    url: str
    page_id: str
    title: str
    icon: str
    is_workspace: bool
    update_datetime: datetime | None


class NotionPageDTO(Schema):
    title: str
    icon: str
    update_datetime: datetime | None

    @classmethod
    def from_notion_page_qs(cls, notion_page_qs):
        return [cls(
            title=item.title,
            icon=item.icon,
            update_datetime=item.modified + timedelta(hours=9)
        ) for item in notion_page_qs]

