from typing import List

from ninja import Schema

from sources.enums import NotionValidErrorEnum
from sources.schemas import NotionPageSchema


class NotionValidPayloadSchema(Schema):
    page_limit_counts: int
    page_counts: int
    notion_page_schemas: List[NotionPageSchema]


class NotionValidErrorSchema(Schema):
    error_code: NotionValidErrorEnum
    payload: NotionValidPayloadSchema
