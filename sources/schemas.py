from typing import List

from ninja import Schema
from pydantic.datetime_parse import datetime

from sources.constants import NOTION_PAGE_LIMIT
from sources.enums import DataSourceEnum


class NotionCallbackParams(Schema):
    code: str
    redirect_url: str


class NotionAccessTokenParams(Schema):
    access_token: str


class SyncStatusSchema(Schema):
    source: DataSourceEnum
    total_page_count: int | None
    current_page_count: int | None
    limit_page_count: int
    is_running: bool
    last_sync_datetime: datetime | None

    @classmethod
    def from_instance(cls, data_sync_status):
        return cls(
            source=data_sync_status.data_source.source,
            total_page_count=data_sync_status.total_page_count,
            current_page_count=data_sync_status.cur_page_count,
            limit_page_count=NOTION_PAGE_LIMIT,
            is_running=data_sync_status.is_running,
            last_sync_datetime=data_sync_status.last_sync_datetime
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
    created_at: datetime | None
    updated_at: datetime | None

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
    description: str | None
    text: str | None
    text_hash: str | None  # original text parsing 로직을 바꾸면 hash 값 업데이트
    icon: str
    is_workspace: bool
    update_datetime: datetime | None


class NotionPagePayloadDTO(Schema):
    title: str
    icon: str


class NotionPageDTO(Schema):
    page_limit_counts: int
    page_counts: int
    notion_page_schemas: List[NotionPagePayloadDTO]
    update_datetime: datetime | None


class DataSourceDTO(Schema):
    id: int
    data_source: DataSourceEnum
    icon: str
    name: str
    description: str
    limit_description: str
    is_available: bool
    is_upvote: bool

    @classmethod
    def from_instances(cls, user, data_source_qs):
        return [
            cls(
                id=data_source.id,
                data_source=data_source.source,
                icon=data_source.icon,
                name=data_source.name,
                description=data_source.description,
                limit_description=cls.get_limit_description(data_source),
                is_available=data_source.is_available,
                is_upvote=True if user.datasourceupvote_set.filter(data_source__source=data_source.source) else False
            )
            for data_source in data_source_qs
        ]

    @classmethod
    def get_limit_description(cls, data_source):
        if data_source.source == DataSourceEnum.notion:
            return f"{data_source.limit_count}페이지 연동 가능"
        else:
            return ""


class MyDataSourceDTO(Schema):
    data_source_type: DataSourceEnum
    icon: str
    account_name: str
    cur_status_description: str
    last_sync_date_description: str
    is_running: bool

    @classmethod
    def from_instances(cls, data_sync_status_qs):
        return [
            cls(
                data_source_type=sync_status.source,
                icon=sync_status.data_source.icon if sync_status.data_source.icon else "",
                account_name=sync_status.account_name if sync_status.account_name else "",
                cur_status_description=cls.get_cur_status_description(sync_status),
                last_sync_date_description=cls.last_sync_date_description(sync_status),
                is_running=cls.get_is_running(sync_status)
            )
            for sync_status in data_sync_status_qs
        ]

    @classmethod
    def get_cur_status_description(cls, sync_status):
        data_source = sync_status.data_source
        if data_source.source == DataSourceEnum.notion:
            cur_page_counts = sync_status.user.notionpage_set.count()
            return f"연동된 페이지 수: ({cur_page_counts}/{data_source.limit_count})"

    @classmethod
    def last_sync_date_description(cls, sync_status):
        if sync_status.data_source.source == DataSourceEnum.notion:
            last_sync_date_str = sync_status.last_sync_datetime.date().strftime("%Y.%m.%d")
            return f"최근연동일자 {last_sync_date_str}"

    @classmethod
    def get_is_running(cls, sync_status):
        data_source = sync_status.data_source
        if data_source.source == DataSourceEnum.notion:
            return sync_status.is_running


class PostUpvoteParams(Schema):
    data_source_id: int
