from typing import List

from ninja import Schema

from sources.enums import NotionValidErrorEnum


class NotionValidPageSchema(Schema):
    title: str
    icon: str


class NotionValidPayloadSchema(Schema):
    page_limit_counts: int
    page_counts: int
    notion_page_schemas: List[NotionValidPageSchema]


class NotionValidErrorDTO(Schema):
    payload: NotionValidPayloadSchema
    error_code: NotionValidErrorEnum
