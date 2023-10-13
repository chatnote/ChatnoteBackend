from typing import List

from ninja import Schema

from sources.enums import DataSourceEnum


class ChatQueryParams(Schema):
    query: str


class ChatReferenceSchema(Schema):
    id: int
    title: str
    url: str
    source: DataSourceEnum


class ChatResponseSchema(Schema):
    query: str
    response: str
    recommend_queries: List[str]
    references: List[ChatReferenceSchema]
