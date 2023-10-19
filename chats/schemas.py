from typing import List

from ninja import Schema

from sources.enums import DataSourceEnum


class ChatQueryParams(Schema):
    query: str


class SearchResponseSchema(Schema):
    title: str
    original_text: str
    chunked_text: str
    url: str | None
    source: DataSourceEnum


class ChatReferenceSchema(Schema):
    title: str
    url: str
    source: DataSourceEnum


class ChatResponseDTO(Schema):
    query: str
    response: str
    recommend_queries: List[str] | None
    references: List[ChatReferenceSchema] | None
